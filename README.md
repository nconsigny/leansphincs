# leanSPHINCS

The [competition site](https://nconsigny.github.io/leansphincs/) carries draft
v0.16: Stage 1 is the academic research track, searching OTS primitives on
pure hash work (oracle calls weighted by input bytes / 64); Stage 2 is the
Ethereum selection track, composing complete stateless schemes under every
deployment gate. Both minimize `size * verification`, with signing work and
keygen work fixed as hard budgets (1.5 s signing, 1 minute keygen at the wallet
anchor), plus the other usability gates and separate hash-work/cycle profiles.
The Stage 1 board has a Spacetime tab (the ranking) and a Pareto tab (the
size/verification frontier at the fixed budgets).

The oracle accepts arbitrary-length inputs and returns **32 bytes**. Hash work is
now `ceil(inputBytes / 64)` per call, including domain-separation bytes; empty
input costs zero hash-work units but still counts as a raw security query.
This is a breaking meter revision (`rom256-input64-ceil-v1`), not a change to
security assumptions. Old 32-byte-unit results must be rechecked, not mixed into
the new profile. Under fixed size/signing constraints, the primitive search does
not assume hash chains are optimal; ROM-secure Reed–Solomon encodings stay in scope.

The rules are published from `index.html` on `main` to GitHub Pages. Publication
mechanics and editing conventions for agents live in [AGENTS.md](AGENTS.md).

See [OTS foundations and proof milestones](OTS_STAGE1.md) and the
[polynomial-coding review](POLYNOMIAL_CODING_REVIEW.md).

This checkout contains the legacy WS2–WS4 MVP statement/harness and experimental
OTS proofs, not an open leaderboard or a complete competition claim with budget certificates. The permanent
challenge home, protected-module governance and independent verifier registration
remain deferred.

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

The legacy receipt still scores only `sigma * hverify` and is unranked. The
positive comparator canary proves only metric statements; it is **not baseline #0**
and makes no security claim. Baseline #0 is intended to be an eligible SPHINCS⁻
variant. Intentional `sorry` and axiom fixtures live outside the protected library
and are rejected by the production import policy.

Signing may explicitly return `none`. The claim separately requires correctness on success and failure probability ≤ 2⁻¹²⁸ for each fixed message under fresh key generation and a shared ROM; a 2⁻²⁵⁶ certificate also qualifies. This does not assert adaptive lifetime availability.

See [implementation contract](IMPLEMENTATION.md), [PR #19 compatibility review](PR19_REVIEW.md), and the [workstream plan](SCHEMECLAIM_PLAN.md). Baseline transport and production validation remain before freezing submissions; the 64-byte input-unit convention is now pinned. The signing-failure decision first appeared in spec v0.13 (R8) on both then-synchronized targets; subsequent revisions are maintained on GitHub.

For implementers: [submission format and proof obligations](SUBMISSION.md).
For operators: [sandbox profile, test commands and launch gates](HARNESS_SECURITY.md).
