#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

args=("$@")
if [[ "${BENCHMARK_INSECURE_LOCAL:-0}" == 1 ]]; then
  echo "Organizer-owned unsandboxed diagnostic; never a ranked result." >&2
  args+=(--insecure-local)
fi
exec python3 scripts/verify_submission.py "${args[@]}"
