#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

readonly comparator_rev=777e7f56119efc0fac34003db4efe831e0b53723
readonly landrun_rev=811cfff51ceaf3d9843708aa6d22e9b84ccac8b4
readonly comparator_dir=.benchmark-tools/comparator

clone_at() {
  local url="$1" revision="$2" destination="$3"
  if [[ ! -d "$destination" ]]; then
    git clone --no-checkout "$url" "$destination"
    git -C "$destination" checkout --detach "$revision"
  fi
  [[ "$(git -C "$destination" rev-parse HEAD)" == "$revision" ]] || {
    echo "tool checkout at unexpected revision: $destination" >&2
    exit 1
  }
  if [[ "$destination" == "$comparator_dir" ]] &&
      git -C "$destination" apply --reverse --check "$PWD/benchmark/comparator-leanchecker.patch" 2>/dev/null; then
    [[ "$(git -C "$destination" diff -- Main.lean)" == "$(<benchmark/comparator-leanchecker.patch)" ]] || {
      echo "unexpected comparator edits" >&2; exit 1;
    }
    [[ -z "$(git -C "$destination" status --porcelain -- . ':!Main.lean')" ]] || {
      echo "unexpected comparator files" >&2; exit 1;
    }
    return
  fi
  [[ -z "$(git -C "$destination" status --porcelain)" ]] || {
    echo "tool checkout contains local changes: $destination" >&2
    exit 1
  }
}

clone_at https://github.com/leanprover/comparator.git "$comparator_rev" "$comparator_dir"
if git -C "$comparator_dir" apply --check "$PWD/benchmark/comparator-leanchecker.patch" 2>/dev/null; then
  git -C "$comparator_dir" apply "$PWD/benchmark/comparator-leanchecker.patch"
fi
toolchain="$(<lean-toolchain)"
lake "+$toolchain" -d "$comparator_dir" build comparator lean4export

if [[ "${BENCHMARK_INSECURE_LOCAL:-0}" != 1 ]]; then
  clone_at https://github.com/Zouuup/landrun.git "$landrun_rev" .benchmark-tools/landrun
  (cd .benchmark-tools/landrun && go build -trimpath -o landrun ./cmd/landrun)
fi

lake exe cache get
lake build LeanSphincs
lake env lean scripts/check-axioms.lean
if [[ "${BENCHMARK_INSECURE_LOCAL:-0}" != 1 ]]; then
  python3 scripts/check-sandbox.py
fi
