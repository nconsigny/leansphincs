# PR #19 and the MVP statement

Reviewed source: [leanEthereum/leanVM-b PR #19](https://github.com/leanEthereum/leanVM-b/pull/19), `sphincs-fv` head `a1daec3b929d8963b4eee4f1e05985065a96de9d`, observed 2026-09-06. The PR is open. Its description says 126 bits are proved and 127 is work in progress. This review concerns statement compatibility and the completed theorem path; it is not an audit of every ongoing 127-bit reduction.

## What is actually stated

[`SphincsSecurity.lean`](https://github.com/leanEthereum/leanVM-b/blob/a1daec3b929d8963b4eee4f1e05985065a96de9d/formal/sphincs/SphincsSecurity.lean) exports `sphincs_has_126_bits_of_classical_security : SphincsSecurity126Statement`, directly using `Concrete.OtsProbeSimulation.security126_of_completed_native_boundary`. The conclusion is unconditional in the sense that it has no user-supplied reduction hypothesis: the adversary and query-bound quantifiers are inside the fixed security statement. The 125- and 120-bit theorems are retained for the same scheme and game. The `securityBits = 120` definition and some older README/AGENTS prose are historical, not the exponent of the new theorem.

[`Statement.lean`](https://github.com/leanEthereum/leanVM-b/blob/a1daec3b929d8963b4eee4f1e05985065a96de9d/formal/sphincs/SphincsSecurity/Statement.lean) fixes a stateless, randomized signature scheme and proves the slope `Adv ≤ q / 2^126` for every nonzero whole-experiment hash budget. The transcript admits at most 2²⁴ signing requests, including failed requests. Repeated messages are allowed; the same message paired with a different valid signature wins. This is SUF-CMA, not just fresh-message EUF-CMA.

The concrete instance has 128-bit internal digests obtained by truncating a 256-bit random oracle, 32-byte messages, target-sum WOTS with 42 chains of length 8 and target sum 191, a 26-level hypertree split 12/7/7, and 14 held few-time trees of height 10. The typed signature contains 4,924 bytes of fields; the public key has two 16-byte fields. These field counts are useful inputs to a byte-serialization proof, not a completed competition size certificate.

## Compatibility

| Concern | PR #19 | Staged MVP / consequence |
| --- | --- | --- |
| Hash oracle | Arbitrary byte string → 256 bits, lazy shared cache | Same oracle semantics and dependency pin |
| Security notion | SUF-CMA, repeated messages allowed | Same winning condition |
| Statelessness | No epoch or mutable signing state | Same |
| Hash budget | Keygen + adversary + signing + final verify; coins excluded | Same, separate from scored weighted cost |
| Signing budget | Transcript-length gate at 2²⁴ | Structural adversary bound at 2²⁰; requires a game/cap transport lemma |
| Signing result | `Option Signature`, with bounded retries | MVP now accepts `Option Bytes`; needs successful-output correctness and a separate ≤ 2⁻¹²⁸ failure certificate |
| Secret generation | Independent uniform secret tables | Fits abstract secret-key freedom; says nothing yet about seed expansion or wallet memory |
| Signature representation | Typed fields | Needs serialization, parsing, rejection of malformed encodings and SUF-preserving transport |
| Verification score | Security counts raw oracle queries | Needs a separate proof charging every input by its 64-byte input-unit weight (v0.15) |
| Security bound | Completed 126-bit slope | Clears 124 numerically; transport still must bind the actual scheme and game |

The same Lean 4.31.0 / VCVio `cbd4144b51d92da00dd50f05e068b2348fa6e529` pin removes a toolchain migration from this adapter's critical path. PR #19 therefore offers a concrete baseline route alongside the independent HashSig oracle-ization work. It does not justify raising the agreed 124-bit entry floor by itself.

## Numerical bridge

The public slope can be encoded exactly as `4*qH / 2^128`, with `bound.txt` equal to `[[4,1,1,0,128]]`. This is 126 bits and passes the MVP's 124-bit floor. The declaration has no `qS` term because the upstream theorem already quantifies over its fixed 2²⁴-request game; a cap-transport proof is still required before using it at 2²⁰.

[`Security126RefinedEndpoint.lean`](https://github.com/leanEthereum/leanVM-b/blob/a1daec3b929d8963b4eee4f1e05985065a96de9d/formal/sphincs/SphincsSecurity/Proof/Security126RefinedEndpoint.lean) checks the more detailed allowance

```text
(10/3) q / 2^128 + 19 q / 2^133 + q / 2^139 + q / 2^216 ≤ q / 2^126.
```

The reduction uses that allowance in its stated bounded-query range, then extends the final slope to larger q using probability ≤ 1. The arithmetic fixtures in `LeanSphincsTest/BoundExamples.lean` reproduce both forms with exact rationals. They do not assert that the refined polynomial is already a globally transported bound in the competition game.

## Verification-cost translation

The paper's cost table gives 497 raw verification hash calls. From the pinned statement's exact input layouts, the v0.15 meter `ceil(inputBytes / 64)` yields the following **source-level calculation**, still requiring a Lean query-bound proof over the byte adapter. The output remains 32 bytes; supplied domain-separation bytes are already included in these lengths:

| Call family | Calls on a full verification path | Input bytes | Units |
| --- | ---: | ---: | ---: |
| Message digest | 1 | 96 | 2 |
| FTS leaves | 14 | 48 | 14 |
| FTS authentication nodes | 140 | 64 | 140 |
| FTS roots hash | 1 | 256 | 4 |
| WOTS encoding | 3 | 52 | 3 |
| WOTS chain steps | 309 | 48 | 309 |
| WOTS public-key leaves | 3 | 704 | 33 |
| Hypertree authentication nodes | 26 | 64 | 26 |
| Total | 497 | | 531 |

An accepted target-sum encoding leaves `42*7 - 191 = 103` chain steps per layer. Malformed digest/encoding branches return early, but a formal worst-case proof must cover those paths too. At 4,924 signature bytes this suggests a legacy MVP product of 2,614,644; it is **not a certified or ranked score**, and is not the new four-factor score. The raw-call and block-weighted metrics must not be substituted for each other. The earlier 1,061-unit estimate used the historical 32-byte input unit, not a different or faster algorithm; it must not be compared as though both estimates used one meter.

## Signing failure: adopted MVP policy (2026-09-06)

The cap on digest attempts and on encoding counters is 2³². Their exhaustion returns `none`; replacing `none` with arbitrary bytes would not prove correctness. Retrying without limit would also change termination and cost obligations. Upstream's `Correctness.eval_verify` proves verification for an honestly constructed signature under explicit construction premises, not probability-one signing success.

The implemented interface is `sign : sk → message → OracleComp OracleWorld (Option Bytes)`. Every request and response, including `none`, belongs to the adversary-visible signing transcript and consumes signing-query budget. Only `some signature` can constitute a replay. Exact signature size applies to every successful output, and the verifier still receives bytes, not an option.

The organizers approved two separate obligations: correctness on successful signing, and `Pr[failure] ≤ 2^-128` for each fixed message in a fresh key-generation/signing experiment sharing one ROM. A 2⁻²⁵⁶ proof also qualifies, via the proved monotonicity lemma. The fresh-experiment gate alone does not establish adaptive lifetime availability or a conditional bound for each key. An always-failing signer satisfies the successful-output clause vacuously but is rejected by the availability gate. Regression fixtures check that separation, invalid successful outputs, replay handling and request accounting.

The public 126-bit security result does not by itself establish this new availability clause. Upstream's `EncodingExhaustionBound.lean` bounds an encoding-exhaustion event by 2⁻²¹⁶, but the complete signing-failure theorem must also cover digest grinding and the actual signing experiment. Transporting or proving that combined bound is still a baseline obligation; it has not been inferred from unforgeability.

## Validation boundaries

The visible successful Lean check on the PR is named `xmss-formalization`. Its workflow builds `formal/xmss` and checks the XMSS theorem's axioms. It does not build `formal/sphincs`. The SPHINCS root also lacks the XMSS-style `#guard_msgs` axiom assertion. These are CI coverage gaps, not evidence that the 126-bit theorem is false.

A local reproduction completed on 2026-09-07 in the durable workspace cache `.benchmark-tools/sphincs-reference`, pinned to the reviewed revision `a1daec3b929d8963b4eee4f1e05985065a96de9d`: `lake build SphincsSecurity.Proof.Security126Completion` finished all 3,479 jobs, and `scripts/check-pr19.lean` passed, so the completed 126-bit statement typechecks and `security126_of_completed_native_boundary` depends on exactly `propext`, `Classical.choice` and `Quot.sound` (the `#guard_msgs` check uses whitespace-lax matching because Lean wraps the axiom list). Reproduce with `bash scripts/check-pr19.sh`. The audit checks the exact completed endpoint against `SphincsSecurity126Statement`, independently of the unfinished 127-bit work. The PR head has since advanced (`a0ffb5476b41f0aa9b6d8c78871f87126e43ca9d` at last check); the public theorem, Statement.lean and Lean CI workflow were unchanged between the snapshots. This review remains pinned to the earlier revision.

The competition implementation itself has passed `lake build LeanSphincs`, its protected axiom audit, 10 host-side contract tests, and all five real-comparator canaries (acceptance, three metric mismatches and a smuggled axiom). The two numerical PR #19 fixtures also compile. No claim of a completed competition baseline, a seed-derived implementation theorem, wallet eligibility, QROM security or a BLAKE2s instantiation follows from these checks.
