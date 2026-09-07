#!/usr/bin/env python3
"""Isolated, content-addressed MVP verification. Reports are never promotions."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from benchmark_contract import metrics, render
from sandbox_profile import systemd_command
from source_bundle import capture, manifest, materialize

ROOT = Path(__file__).resolve().parents[1]
COMPARATOR = ROOT / ".benchmark-tools/comparator"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def harness_manifest() -> dict:
    files = [ROOT / name for name in ("lakefile.toml", "lake-manifest.json", "lean-toolchain",
                                      "LeanSphincs.lean", "benchmark.sh", "setup.sh")]
    for folder in ("scripts", "benchmark", "LeanSphincs/Benchmark"):
        files += [p for p in (ROOT / folder).iterdir()
                  if p.is_file() and p.name != "Challenge.lean"]
    return manifest({str(p.relative_to(ROOT)): p.read_bytes() for p in files})


def check_dependencies() -> dict:
    packages = json.loads((ROOT / "lake-manifest.json").read_text())["packages"]
    revisions = {}
    for package in packages:
        path = ROOT / ".lake/packages" / package["name"]
        revision = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        if package["type"] != "git" or revision != package["rev"]:
            raise RuntimeError(f"dependency pin mismatch: {package['name']}")
        dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain",
                                         "--untracked-files=no"], text=True)
        if dirty:
            raise RuntimeError(f"tracked dependency changes: {package['name']}")
        revisions[package["name"]] = revision
    return revisions


def prepare_project(project: Path, bundle: dict[str, bytes], source: str) -> None:
    project.mkdir()
    for name in ("lakefile.toml", "lake-manifest.json", "lean-toolchain", "LeanSphincs.lean"):
        shutil.copy2(ROOT / name, project / name)
    shutil.copytree(ROOT / "LeanSphincs/Benchmark", project / "LeanSphincs/Benchmark",
                    ignore=shutil.ignore_patterns("Challenge.lean"))
    materialize(bundle, project / "LeanSphincs/Submission")
    (project / "LeanSphincs/Benchmark/Challenge.lean").write_text(source)
    (project / ".lake").mkdir()
    (project / ".lake/packages").symlink_to(ROOT / ".lake/packages", target_is_directory=True)
    # Only organizer artifacts: no shared writable cache or stale submission .oleans.
    if (ROOT / ".lake/config").exists():
        shutil.copytree(ROOT / ".lake/config", project / ".lake/config")
    for facet in ("lib/lean", "ir"):
        cached = ROOT / f".lake/build/{facet}/LeanSphincs/Benchmark"
        if cached.exists():
            shutil.copytree(cached, project / f".lake/build/{facet}/LeanSphincs/Benchmark",
                            ignore=shutil.ignore_patterns("Challenge.*"))
        (project / f".lake/build/{facet}/LeanSphincs/Submission").mkdir(parents=True)
    (project / "home").mkdir()
    shutil.copy2(ROOT / "benchmark/comparator.json", project / "comparator.json")
    for name in ("strict-landrun.py", "sandbox_profile.py", "check-axioms.lean"):
        shutil.copy2(ROOT / "scripts" / name, project / name)
    (project / "strict-landrun.py").chmod(0o700)


def run(command: list[str], project: Path, env: dict, log: Path, timeout: int = 4800) -> int:
    with log.open("wb") as output:
        process = subprocess.Popen(command, cwd=project, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   start_new_session=True)
        try:
            return process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            units = [arg.removeprefix("--unit=") for arg in command if arg.startswith("--unit=leansphincs-")]
            try:
                for unit in units:
                    subprocess.run(["systemctl", "--user", "stop", unit], env=dict(os.environ),
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, timeout=15)
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            raise


def verify(submission: Path, insecure: bool = False) -> tuple[dict, Path]:
    result_root = ROOT / "benchmark-results/runs"
    result_root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="run-", dir=result_root))
    os.chmod(directory, 0o700)
    report = {"schema": "leansphincs-verification-v1", "ranked": False,
              "profile": "insecure-local" if insecure else "leansphincs-linux-v1",
              "status": "infrastructure_error", "started_unix": int(time.time())}
    stage = "capture"
    try:
        bundle = capture(submission)
        report["submission"] = manifest(bundle)
        stage = "source_policy"
        materialize(bundle, directory / "source")
        sigma, hverify, bound = metrics(directory / "source")
        check = subprocess.run(["bash", str(ROOT / "scripts/check-submission-imports.sh"),
                                str(directory / "source")], capture_output=True, text=True)
        if check.returncode:
            raise ValueError(check.stderr.strip() or check.stdout.strip())
        report["metrics"] = {"sigma": sigma, "hverify": hverify, "bound": bound}
        stage = "setup"
        report["harness"] = harness_manifest()
        report["dependencies"] = check_dependencies()
        lean = Path(subprocess.check_output(["lean", "--print-prefix"], cwd=ROOT, text=True).strip())
        tool_paths = {"comparator": COMPARATOR / ".lake/build/bin/comparator",
                     "exporter": COMPARATOR / ".lake/packages/lean4export/.lake/build/bin/lean4export",
                     "lean": lean / "bin/lean", "leanchecker": lean / "bin/leanchecker"}
        landrun = ROOT / ".benchmark-tools/landrun/landrun"
        if not insecure:
            tool_paths["landrun"] = landrun
        report["tools"] = {name: digest(path) for name, path in tool_paths.items()}
        if not insecure:
            stage = "sandbox_preflight"
            spec = importlib.util.spec_from_file_location("check_sandbox", ROOT / "scripts/check-sandbox.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            report["sandbox"] = module.check(lean, tool_paths["exporter"], landrun)
        stage = "trusted_build"
        project = directory / "project"
        prepare_project(project, bundle, render(sigma, hverify, bound))
        (project / "sandbox.json").write_text(json.dumps({"lean_prefix": str(lean),
            "exporter": str(tool_paths["exporter"]), "landrun": str(landrun)}))
        env = {"PATH": f"{lean}/bin:/usr/bin:/bin", "HOME": str(project / "home"),
               "LANG": "C.UTF-8", "LEAN_ABORT_ON_PANIC": "1"}
        # Challenge imports protected definitions only, never candidate code.
        if run([str(lean / "bin/lake"), "build", "LeanSphincs.Benchmark.Challenge", "LeanSphincs"],
               project, env, directory / "trusted-build.log"):
            raise RuntimeError("trusted template build failed; see trusted-build.log")
        if run([str(lean / "bin/lake"), "env", "lean", "check-axioms.lean"], project,
               env, directory / "axioms.log"):
            raise RuntimeError("protected axiom audit failed; see axioms.log")
        env.update(COMPARATOR_LEAN4EXPORT=str(tool_paths["exporter"]),
                   COMPARATOR_LANDRUN=str(COMPARATOR / "scripts/fake-landrun.sh") if insecure
                   else str(project / "strict-landrun.py"))
        stage = "comparison"
        command = [str(lean / "bin/lake"), "env", str(tool_paths["comparator"]), "comparator.json"]
        if not insecure:
            command = systemd_command(command, project, env)
        # Only the trusted systemd client needs the user's bus locator. The
        # service itself starts through env -i with the explicit clean env.
        code = run(command, project, env if insecure else dict(os.environ), directory / "comparator.log")
        report["comparator_exit"] = code
        report["status"] = "accepted" if code == 0 else "verification_failed"
        stage = "integrity"
        if manifest(capture(project / "LeanSphincs/Submission")) != report["submission"]:
            raise RuntimeError("snapshot changed during verification; no score issued")
        if harness_manifest() != report["harness"]:
            raise RuntimeError("harness changed during verification; no score issued")
        if code == 0:
            report["score"] = {"value": str(sigma * hverify), "direction": "minimize", "tie_break": sigma}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report.pop("score", None)
        report["status"] = "source_rejected" if stage in {"capture", "source_policy"} else "infrastructure_error"
        report["error"] = str(error)
    except KeyboardInterrupt:
        report.pop("score", None)
        report["status"] = "interrupted"
        report["error"] = "verification interrupted; worker stop requested"
    report["stage"] = stage
    report["finished_unix"] = int(time.time())
    report["logs"] = {p.name: digest(p) for p in directory.glob("*.log")}
    (directory / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report, directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", nargs="?", type=Path, default=ROOT / "LeanSphincs/Submission")
    parser.add_argument("--insecure-local", action="store_true", help="organizer-owned diagnostics only")
    args = parser.parse_args()
    report, directory = verify(args.submission, args.insecure_local)
    print(json.dumps({"status": report["status"], "ranked": False, "result": str(directory / "result.json"),
                      **({"error": report["error"]} if "error" in report else {})}))
    sys.exit(0 if report["status"] == "accepted" else 1)
