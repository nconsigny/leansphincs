# Verifier trust boundary and launch gates

Status: staged engineering profile, 2026-09-07. Not an external security audit,
registered verifier, open leaderboard or accepted baseline.

## Submission path

`bash benchmark.sh /path/to/submission` captures a flat folder, validates the
captured bytes, prepares a private Lake project, compiles its protected challenge,
audits the protected axioms, then runs the real comparator in the Linux profile.
The comparator builds candidate modules, rechecks them with `leanchecker`, exports
their statements, compares against the rendered claim and checks axiom closure.

Each run retains `source/`, `project/`, logs and `result.json` in a distinct
mode-0700 directory under `benchmark-results/runs/`. The receipt binds filenames,
source bytes, all three metrics, harness sources, dependency Git pins, tool-binary
hashes and log hashes. A score is emitted only after successful comparison and a
post-run input/harness integrity check. Every receipt says `ranked: false`.

The statuses are `source_rejected`, `infrastructure_error`, `verification_failed`,
`interrupted` and `accepted`. `verification_failed` can include a compiler/tool error, not just
a false theorem; consult its log. Rejections never emit a score. Receipts are local
evidence, not signed attestations or authority to award/promote a submission.

## Filesystem and cache isolation

- Directory-relative `O_NOFOLLOW` opens capture inputs once. FIFOs, symlinks,
  nested directories, non-UTF-8/NUL source and ambiguous Lean filenames are rejected.
  The accepted bytes need not describe a simultaneous state of a changing live
  directory: those captured bytes themselves define the submitted artifact.
- Each run has independent generated source and candidate build outputs. No prior
  candidate `.olean` is copied. There is no shared generated `Challenge.lean`.
- Pinned dependency caches are read-only to candidate processes. Protected source,
  configuration and compiled modules are also read-only. Only the two candidate
  output directories under `.lake/build/{lib/lean,ir}/LeanSphincs/Submission` are
  writable, plus `/dev/null`. Candidate-generated files cannot be executed.
- The inherited comparator's filesystem-wide reads and `.lake` write grant are
  replaced by `strict-landrun.py`; incoming permission flags are not forwarded.
  User home, Git credentials and arbitrary project siblings are not read grants.
- Trusted challenge preparation runs before candidate compilation and imports only
  protected modules. It can use organizer dependency caches. The source parser is
  a defense-in-depth policy, not the operating-system security boundary.

## Linux profile: mandatory, actively checked

The profile requires Linux x86-64 or AArch64, Landlock ABI **at least 8**, a user
systemd manager with cgroup limits and seccomp filtering, and the setup-pinned
Landrun/comparator/toolchain. It never falls back automatically to no sandbox.

Pinned [Landrun source](https://github.com/Zouuup/landrun/tree/811cfff51ceaf3d9843708aa6d22e9b84ccac8b4)
targets ABI 9. We explicitly allow ABI 8 compatibility with its `--best-effort`
option only after enforcing the ABI floor. The missing pathname Unix-socket
restriction is covered by systemd's mandatory denial of the entire `@network-io`
system-call group. TCP, UDP and Unix sockets are all probed for denial. This is
an explicit composite profile, not a claim that ABI 8 supplies ABI 9 features.

Limits: 24 GiB memory, no swap, 256 tasks, 80 minutes, 2 GiB per output file,
no core dumps, no new privileges. Network I/O, mount, reboot, swap, raw-I/O and
debug syscall groups are denied. The service receives a clean environment and a
private HOME and closed stdin. Each service has a unique unit name; timeout or
cancellation requests a stop of its whole cgroup, not just the waiting client.

`python3 scripts/check-sandbox.py` runs synthetic positive/negative probes using the
same resource/permission constructors as verification. It checks outside-file
reads; protected, dependency and source writes; TCP, UDP, IPv6 and Unix sockets;
and allowed candidate-output writes. A probe failure is an infrastructure error.
`BENCHMARK_INSECURE_LOCAL=1` is only an explicit organizer diagnostic mode.

Local validation on 2026-09-07 passed all eleven boundary checks, all five
sandboxed metric canaries, all four actual-claim rejection cases, 22 host tests
and the Lean library/test builds. This is evidence for this checkout/host, not
an independent audit or a remote CI/deployment result.

## Tests and remaining launch work

```sh
bash setup.sh
python3 -m unittest discover -s tests -v
lake build LeanSphincs LeanSphincsTest
python3 scripts/test-comparator.py       # organizer metric canaries, unsandboxed
python3 scripts/test-sandbox-comparator.py # same metric cases in the real sandbox
python3 scripts/test-verifier.py         # actual SchemeClaim negative path, sandboxed
```

The five comparator canaries prove only metric statements. The production-path
negatives use the real rendered `SchemeClaim`: forged axiom, `sorry`, weakened
statement and a computation reaching outside the oracle type. They must fail for
the intended reason, not merely because compilation or sandbox setup is broken.

Ordinary GitHub-hosted CI runs the host/Lean tests and explicitly unsandboxed
organizer fixtures. The manual `sandbox.yml` workflow is restricted to `main`
and requires a separately provisioned disposable, credential-free Linux worker
labelled `leansphincs-verifier`. It has not been registered or run remotely by
this implementation. The workflow retains test logs and receipts for 14 days.

Before opening submissions:

1. Land baseline #0 with the actual security-game/serialization transport,
   verification-cost proof and signing-failure certificate. Mutate that accepted
   baseline to complete the full production-profile negative matrix.
2. Review and freeze the block convention, protected modules and governance.
3. Build a reproducible, independently controlled verifier image. Source Git pins
   and recorded binary hashes alone do not authenticate precompiled dependency
   artifacts. Organizer caches/tool installation remain trusted inputs here.
4. Run the external harness audit; pin the operating-system/systemd/tool versions
   and validate the profile on its dedicated worker. Do not run an untrusted PR
   on a credential-bearing persistent self-hosted runner.
5. Add worker-queue concurrency/aggregate disk quotas, log-retention policy and
   signed verifier receipts. Per-file/process limits are not an aggregate disk
   quota. Local runs retain artifacts; an operator must manage retention.
6. Add reviewed frontier promotion/credit and website ingestion of authenticated
   results. Do not let a submitted JSON receipt promote itself. Wallet/cycle gates
   and full-track rules remain separate unfinished work.

The threat model excludes an attacker who already controls the verifier's Unix
account, trusted dependencies, tool binaries or kernel. Run directories protect
against candidate subprocesses, not an independent same-user process editing
organizer files. No cryptographic eligibility or launch readiness follows merely
from passing the harness tests.
