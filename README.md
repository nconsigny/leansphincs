# leanSPHINCS

The [competition spec](https://nconsigny.github.io/leansphincs/) is at draft v0.13. This checkout also stages the WS2–WS4 MVP statement and harness. The permanent challenge home, protected-module governance and independent verifier registration remain deferred.

The implementation builds against Lean 4.31.0 and the same pinned VCVio revision as the XMSS and SPHINCS proof references. It contains the shared random-oracle SUF-CMA game, exact rational bound evaluator with a proved endpoint test, byte-exact size and weighted verification claims, and a comparator with one scheme-definition hole.

```sh
# Organizer-owned development checkout only; these local diagnostics are unranked.
BENCHMARK_INSECURE_LOCAL=1 bash setup.sh
python3 -m unittest discover -s tests -v
lake build LeanSphincsTest.BoundExamples LeanSphincsTest.SigningFailure
python3 scripts/test-comparator.py
```

For a candidate, put `Scheme.lean`, `Solution.lean`, `sigma.txt`, `hverify.txt` and `bound.txt` in a flat folder, then run `bash benchmark.sh /path/to/folder` (default: `LeanSphincs/Submission/`). Each run gets a private source snapshot/build project and a content-bound `result.json` with logs under `benchmark-results/runs/`. No candidate build cache is reused.

The default Linux profile requires Landlock ABI ≥ 8 and a user systemd instance; active filesystem/network probes must pass. Run `bash setup.sh`, then `python3 scripts/test-verifier.py` for the real submission-path rejection tests. An explicit `BENCHMARK_INSECURE_LOCAL=1` permits an organizer-owned unsandboxed diagnostic. Neither path produces an authoritative ranking. See [trust boundary and launch gates](HARNESS_SECURITY.md).

The positive comparator canary proves only metric statements; it is **not baseline #0** and makes no security claim. Intentional `sorry` and axiom fixtures live outside the protected library and are rejected by the production import policy.

Signing may explicitly return `none`. The claim separately requires correctness on success and failure probability ≤ 2⁻¹²⁸ for each fixed message under fresh key generation and a shared ROM; a 2⁻²⁵⁶ certificate also qualifies. This does not assert adaptive lifetime availability.

See [implementation contract](IMPLEMENTATION.md), [PR #19 compatibility review](PR19_REVIEW.md), and the [workstream plan](SCHEMECLAIM_PLAN.md). Baseline transport, production validation and review of the staged block convention remain before freezing submissions. The signing-failure decision is published in spec v0.13 (R8) on both targets.

For implementers: [submission format and proof obligations](SUBMISSION.md).
For operators: [sandbox profile, test commands and launch gates](HARNESS_SECURITY.md).
