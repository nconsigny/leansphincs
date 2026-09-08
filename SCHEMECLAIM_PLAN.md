# SchemeClaim: build plan for the leanSPHINCS statement layer

Status: draft for team review, 2026-09-02; local implementation progress added 2026-09-06. Companion to the [competition spec](https://nconsigny.github.io/leansphincs/), sections 4, 7 and OQ-1/OQ-8.

## Local implementation progress (2026-09-06)

2026-09-09 shipping progress: receipt integrity and SIGTERM handling were committed
and pushed unsigned in `e639597` (no co-author trailer). The next harness batch
adds per-checkout admission locking and retryable `worker_busy` receipts before
candidate access, with 45 host tests. This advances worker admission, not the
remaining external scheduler, aggregate disk quota or cryptographic baseline.

2026-09-09 independent harness work: cooperative CLI SIGTERM cleanup now follows
the interruption path, with process-group and systemd-stop regression coverage
(37 host tests). The OTS target, composition contract and audited reference pin
remain untouched. Emile's branch advanced to
[`68a0bac`](https://github.com/leanEthereum/leanVM-b/commit/68a0bacd9fb8456a8a4c25717cbb83bf9ea6c5fc),
whose commit report leaves the public 126-bit statement unchanged and the final
127-bit theorem open. That revision has not been rebuilt locally here.

2026-09-08 independent harness work: receipts now recheck dependency pins and
tool hashes before scoring and publish complete JSON atomically; 33 host tests
cover integrity drift, orchestration failures and receipt publication. The core
and first sandbox hardening were committed in `31a5f92`; spec v0.13 followed in
`4ae1d37`. These receipt changes do not modify the protected Lean claim.

Coordination: leave the proposed OTS target and composition contract open while
Emile (GitHub `TomWambsgans`) completes his exploration. Monitor
[sphincs-fv](https://github.com/leanEthereum/leanVM-b/tree/sphincs-fv) before
integration; do not move the reproduced PR #19 pin automatically. The branch
snapshot `990b2ce5fa1ee99d8a0797da163db46bc498cf7f` reports reduction improvements
and explicitly leaves the final 127-bit inequality open. This is an upstream
commit report, not a local reproduction of that revision.

2026-09-07 harness advance: per-run source capture and isolated build outputs,
read-only protected/dependency caches, mandatory Linux sandbox probes and
content-bound receipts are implemented. All four real `SchemeClaim` rejection
cases and all five metric-only canaries pass in the strict Linux profile; 22
host tests pass. See [HARNESS_SECURITY.md](HARNESS_SECURITY.md).
This advances WS5 without claiming baseline #0, external audit, registration or
production freeze is complete.

WS2, WS3 and WS4 now have a staged implementation in this checkout, documented in [IMPLEMENTATION.md](IMPLEMENTATION.md). The protected Lean library builds on Lean 4.31.0 / VCVio `cbd4144b51d92da00dd50f05e068b2348fa6e529`; its axiom audit admits only the three standard axioms. The exact rational floor predicate has a proved two-endpoint characterization. The comparator has one scheme-definition hole and binds all three declared metric files. Organizer canaries exercise successful matching, rejection of each changed metric, and forbidden-axiom rejection; they are not baseline #0.

Verified again on 2026-09-07 after the previous session was cut off: the protected library builds, the axiom audit passes, the ten host-side contract tests pass, the signing-failure regression fixtures (always-failing signer rejected, invalid successful output rejected, failed requests charged to the signing budget, `none` never counts as replay) compile, the five comparator canary fixtures were recreated for the `Option Bytes` signing interface and all five real-comparator runs return the expected verdicts, and the PR #19 126-bit endpoint was reproduced locally with a standard-axiom footprint (see PR19_REVIEW.md). A `LeanSphincsTest.lean` root now lets `lake build LeanSphincsTest` succeed. This work was subsequently committed in `31a5f92`.

The staged WS2 block convention is `max(1, ceil(inputBytes / 32))`, charging all supplied bytes, including domain separation. This is an implementation decision for review before freeze. The public spec is at v0.13 (2026-09-07), which carries the signing-failure decision; the block convention below is still an implementation choice for review. Repo home and merge rights remain deferred.

[leanVM-b PR #19](https://github.com/leanEthereum/leanVM-b/pull/19) supplies an additional, directly relevant stateless SUF-CMA proof route: a public 126-bit statement at 2²⁴ signing requests, with the same whole-experiment ROM accounting. See [PR19_REVIEW.md](PR19_REVIEW.md). It can shorten WS6 without waiting for WS1, but needs serialization, game/cap transport and block-weighted verification proofs. Its signer returns `Option Signature` after bounded grinding. Following discussion with Emile and organizer approval on 2026-09-06, the staged contract now admits explicit signing failure, with separate correctness-on-success and failure-probability ≤ 2⁻¹²⁸ obligations. This is a per-fixed-message, fresh-key/shared-ROM gate, not an adaptive lifetime guarantee. Baseline transport and production validation remain; the contract is not yet frozen for submissions.

## What we are building

`SchemeClaim` is the protected, scheme-parametric Lean statement at the heart of the competition. It must:

1. pin the oracle and the security game, leaving exactly one free slot: the submission's scheme;
2. certify every scored quantity inside Lean (signature size, verification compression-call count, the canonical-form security bound and its bit-security floor), so the main leaderboard is a pure proof artifact;
3. be render-and-match compatible with the proximity-prize comparator pipeline (declared metric files rendered into a `Challenge.lean`, exported theorem matched exactly, axioms checked against the permitted list).

## The key sequencing decision (Quang's flag)

The current `HashSig.SLHDSA` development keeps the hash family opaque but *deterministic*: primitives are pure fields of a `Primitives` bundle, and `Security.lean` packages them into standard-model interfaces (SM-DT-TCR, SM-DT-PRE, PRF games). The competition statement needs the random-oracle model: primitives as `OracleComp` queries with query counting.

The consequence for planning: **this gap blocks reusing HashSig components, not building SchemeClaim**. A submission defines its scheme directly against the pinned game and oracle spec; HashSig is the component library submitters (and our baseline) will want, not a dependency of the statement. So the HashSig oracle-ization runs as a parallel library track, off the critical path.

The template for the statement itself already exists: `formal/xmss/XmssSecurity/Statement.lean` on leanVM-b's `xmss-fv` branch builds a strong-unforgeability experiment, random-oracle simulation, and whole-experiment query accounting from `VCVio.OracleComp.QueryTracking.{LoggingOracle, RandomOracle.Simulation, QueryBound}`. SchemeClaim is, to first order, that file made scheme-parametric.

## Module layout

New challenge repo, skeleton forked from `proximity-prize/proximity-prize`:

```
LeanSphincs/
  Benchmark/                  -- protected: submissions may import, never modify
    Oracle.lean               -- the MVP oracle: N B → 32 B ideal compression function as an OracleSpec
    SchemeInterface.lean      -- SigScheme: types, keygen/sign/verify in OracleComp, serialization
    Game.lean                 -- EUF-CMA / SUF experiment, adversary type, query accounting
    Bound.lean                -- canonical-form bounds: coefficient lists, evalBound, bitSecurity (decidable)
    Claim.lean                -- structure SchemeClaim, bundling 1-5 below
    Target.lean               -- what render-benchmark-challenge instantiates
  Submission/                 -- the free slot: flat root, size-limited, import-checked
    Scheme.lean               -- the scheme definition
    Solution.lean             -- candidate : SchemeClaim Submission.scheme sigma hverify coeffs
    sigma.txt  hverify.txt  bound.txt   -- declared metrics, rendered into Challenge.lean
  Baseline/                   -- organizer baseline #0 (a full worked Submission)
```

## The claim, in shape

Illustrative summary; the normative version is now `LeanSphincs/Benchmark/Claim.lean`.

```lean
structure SchemeClaim (S : SigScheme)
    (sigmaBytes hVerify : Nat) (coeffs : BoundCoeffs) : Prop where
  correct        : CorrectOnSuccess S
  signing_failure : HasSigningFailureBound S 128
  sigma_positive : 0 < sigmaBytes
  sigma_size     : HasSignatureSize S sigmaBytes
  public_key_size : HasPublicKeySize S 64
  hverify_positive : 0 < hVerify
  verify_queries : HasVerificationBound S hVerify
  security       : ∀ (A : Adversary) (qH : Nat),
                     HasHashQueryBound S A qH → HasSigningQueryBound A (2 ^ 20) →
                     sufAdvantage S A ≤ boundProbability coeffs qH (2 ^ 20)
  floor          : MeetsFloor coeffs (2 ^ 20) 124   -- rational certificate via norm_num
```

Notes:

- **The game and oracle come from the protected module.** The import checker admits only `Mathlib`, `VCVio`, `HashSig`, the protected `LeanSphincs.Benchmark.Target`, and flat local helpers. The comparator leaves only `S` as a definition hole; the statement and all metrics must match.
- **Every scored quantity is certified in-Lean.** `sigma_size` via the byte-exact serialization spec; `verify_queries` via VCVio's query-bound machinery (`HashSig` already ships `GeneralSchemeQueryBound.lean`, and xmss-fv counts queries across a whole experiment); `floor` as a decidable predicate over declared coefficients. The rule auditor planned in spec OQ-1 as external tooling disappears into the claim structure.
- **Oracle access by type.** A scheme's algorithms live in the protected `OracleComp` interface. This prevents unmodelled oracle/IO effects, but arbitrary pure computations remain expressible. The unconditional ROM proof, axiom check and rule review enforce the stronger restriction against extra cryptographic assumptions; the type alone is not a complete construction classifier.
- **Statelessness by type.** The game re-runs `sign` from `(sk, msg)` on every signing query; there is no state slot to thread.
- **Availability is separate from security.** Signing returns `Option Bytes`; successful output must verify with probability one, and for each fixed message fresh key generation and signing must return `none` with probability at most 2⁻¹²⁸. Failed responses remain visible and consume query budget; only successful message/signature pairs count as replay. Exact size applies to successful outputs. A 2⁻²⁵⁶ failure certificate is stronger and also accepted.
- MVP simplifications applied (spec section 7): single oracle, q_S ≤ 2^20 only (no decay clause), plain floor at 124, score computed by the harness from the declared `sigma.txt` and `hverify.txt` that the theorem certifies.

## Workstreams

**Phase 1, parallel.**

- **WS1 — HashSig oracle-ization (library track; Quang and Alex's work).** Generalize the `Primitives` bundle so hash fields are monadic (`Thash : PkSeed → AdrsKey → List Y → m Y`), with the existing deterministic layer as the `Id` instantiation and a ROM instantiation over `OracleComp`. Existing concrete instances and KATs must keep compiling. Deliverable: WOTS/XMSS/FORS/hypertree components usable inside a `SigScheme`. Coordinate with the NIST + EasyCrypt-aligned rework already in progress; this plan should not duplicate that branch.
- **WS2 — Benchmark core (`Oracle`, `SchemeInterface`, `Game`).** Port the xmss-fv Statement.lean shapes from concrete-XMSS to scheme-parametric. Decided (2026-09-02): SUF-CMA, and an N B → 32 B oracle with variable-length input; calls are weighted by input length in 32-byte blocks for the score, and the exact block convention is pinned here.
- **WS3 — `Bound.lean`.** Standalone and small: coefficient lists, `evalBound`, `bitSecurity` as a computable function with `decide`-friendly lemmas, `#guard` unit tests. No dependencies on WS1/WS2; a good first PR.

**Phase 2, after WS2 + WS3.**

- **WS4 — `Claim.lean` + `Target.lean` + harness adaptation.** Write the claim structure; adapt `comparator.json` (theorem name, permitted axioms `propext / Quot.sound / Classical.choice`), the render script (three declared files instead of two), and the import allowlist. Pin the toolchain; wire `#guard_msgs` axiom pinning after the xmss-fv pattern.
- **WS5 — Negative tests.** A submission with a wrong `sigma.txt` must be refused; a smuggled axiom must be refused; a scheme reaching outside the oracle spec must fail to typecheck; an import outside the allowlist must be refused at fetch. These tests are the harness's own KATs and ship in CI.

**Phase 3, validates everything end to end.**

- **WS6 — Baseline #0.** A full worked submission by the organizers: a stateless SLH-DSA-style instance built from WS1 components (C13-flavored if ready, a plain small hypertree if not), its `SchemeClaim` proof, and its declared metrics. This is the schedule risk: the security proof is the heavy half. Two mitigations: start from the xmss-fv proof spine (its cache-replay and query-accounting lemmas transfer), and if needed launch with a reduced-parameter instance whose bound closes quickly, upgrading the baseline after launch. The leaderboard needs one honest entry, not a record.

## Decisions (closed 2026-09-02 unless noted)

1. **SUF-CMA** is the pinned notion (matches the xmss-fv precedent).
2. **N B → 32 B oracle** with variable-length input; a fixed 96 B → 32 B would tailor the model to SHA-2. Score weight per call = input length in 32-byte blocks; the exact block convention (N versus N − 1 chaining units) is pinned in WS2.
3. **`sigma_size` is an equality**; fixed-length serialization, pad if needed.
4. **Floor stays at 124** for the MVP; 127 remains the full-track ambition (spec OQ-7).
5. Repo home and protected-module merge rights: **deferred**, to be settled before anyone submits.
6. **Bounded signing failure** (2026-09-06): explicit `none`, correctness on success, and a separate `Pr[none] ≤ 2⁻¹²⁸` theorem per fixed message under fresh key generation and a shared ROM. Stronger bounds such as 2⁻²⁵⁶ qualify. This does not change the 124-bit security floor or add a scored metric. Synchronized to both published spec targets as v0.13 on 2026-09-07 (R8, R2 and the grinding entry of section 9).

## What this plan deliberately leaves out

The RISC-V metering environment (views and the sanity cycle cap) is tracked separately; the current MVP harness does not certify a cycle cap. Wallet-vector gating, presign/cache game clauses and the trick-template library are full-track work requiring a versioned protected claim and review. They must not be advertised as enforced by the present MVP statement.
