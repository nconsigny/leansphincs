# SchemeClaim: build plan for the leanSPHINCS statement layer

Status: draft for team review, 2026-09-02. Companion to the [competition spec](https://nconsigny.github.io/leansphincs/), sections 4, 7 and OQ-1/OQ-8.

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
    Oracle.lean               -- the MVP oracle: ideal compression function as an OracleSpec
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

Illustrative; the normative version is the deliverable of WS4.

```lean
structure SchemeClaim (S : SigScheme oracleSpec)
    (sigmaBytes hVerify : Nat) (coeffs : BoundCoeffs) : Prop where
  correct        : PerfectlyCorrect S
  sigma_size     : SerializedSize S = sigmaBytes
  verify_queries : IsQueryBound S.verify hVerify
  security       : ∀ (A : Adversary oracleSpec) (qH : Nat),
                     A.queries ≤ qH → A.sigQueries ≤ 2 ^ 20 →
                     eufAdvantage S A ≤ evalBound coeffs qH (2 ^ 20)
  floor          : 124 ≤ bitSecurity coeffs (2 ^ 20)   -- closes by decide / norm_num
```

Notes:

- **The game and oracle come from the protected module.** The import checker (reused from proximity-prize) admits only `Mathlib`, `VCVio`, `HashSig`, and `LeanSphincs.Benchmark` from a submission root, so the only thing a submission can contribute is `S` and the proof.
- **Every scored quantity is certified in-Lean.** `sigma_size` via the byte-exact serialization spec; `verify_queries` via VCVio's query-bound machinery (`HashSig` already ships `GeneralSchemeQueryBound.lean`, and xmss-fv counts queries across a whole experiment); `floor` as a decidable predicate over declared coefficients. The rule auditor planned in spec OQ-1 as external tooling disappears into the claim structure.
- **Oracle-only by type.** A scheme is a `SigScheme oracleSpec`: its algorithms live in `OracleComp oracleSpec`, so MPCiTH-style constructions needing a concrete hard problem cannot even be stated (spec R1/OQ-5, enforced by the type checker rather than an audit).
- **Statelessness by type.** The game re-runs `sign` from `(sk, msg)` on every signing query; there is no state slot to thread.
- MVP simplifications applied (spec section 7): single oracle, q_S ≤ 2^20 only (no decay clause), plain floor at 124, score computed by the harness from the declared `sigma.txt` and `hverify.txt` that the theorem certifies.

## Workstreams

**Phase 1, parallel.**

- **WS1 — HashSig oracle-ization (library track; Quang and Alex's work).** Generalize the `Primitives` bundle so hash fields are monadic (`Thash : PkSeed → AdrsKey → List Y → m Y`), with the existing deterministic layer as the `Id` instantiation and a ROM instantiation over `OracleComp`. Existing concrete instances and KATs must keep compiling. Deliverable: WOTS/XMSS/FORS/hypertree components usable inside a `SigScheme`. Coordinate with the NIST + EasyCrypt-aligned rework already in progress; this plan should not duplicate that branch.
- **WS2 — Benchmark core (`Oracle`, `SchemeInterface`, `Game`).** Port the xmss-fv Statement.lean shapes from concrete-XMSS to scheme-parametric. Main design questions to settle in review: SUF (as xmss-fv proves) versus plain EUF-CMA; fixed 96 B → 32 B oracle versus N → 32 B with declared arity.
- **WS3 — `Bound.lean`.** Standalone and small: coefficient lists, `evalBound`, `bitSecurity` as a computable function with `decide`-friendly lemmas, `#guard` unit tests. No dependencies on WS1/WS2; a good first PR.

**Phase 2, after WS2 + WS3.**

- **WS4 — `Claim.lean` + `Target.lean` + harness adaptation.** Write the claim structure; adapt `comparator.json` (theorem name, permitted axioms `propext / Quot.sound / Classical.choice`), the render script (three declared files instead of two), and the import allowlist. Pin the toolchain; wire `#guard_msgs` axiom pinning after the xmss-fv pattern.
- **WS5 — Negative tests.** A submission with a wrong `sigma.txt` must be refused; a smuggled axiom must be refused; a scheme reaching outside the oracle spec must fail to typecheck; an import outside the allowlist must be refused at fetch. These tests are the harness's own KATs and ship in CI.

**Phase 3, validates everything end to end.**

- **WS6 — Baseline #0.** A full worked submission by the organizers: a stateless SLH-DSA-style instance built from WS1 components (C13-flavored if ready, a plain small hypertree if not), its `SchemeClaim` proof, and its declared metrics. This is the schedule risk: the security proof is the heavy half. Two mitigations: start from the xmss-fv proof spine (its cache-replay and query-accounting lemmas transfer), and if needed launch with a reduced-parameter instance whose bound closes quickly, upgrading the baseline after launch. The leaderboard needs one honest entry, not a record.

## Decisions to close before WS4 freezes the statement

1. SUF or EUF-CMA as the pinned notion (xmss-fv precedent says SUF).
2. Oracle arity: fixed 96 B → 32 B or N B → 32 B with cost-by-N (spec section 7, item 3).
3. `sigma_size` as equality or upper bound (equality is cleaner for the comparator; padding makes it harmless).
4. MVP floor stays 124 or moves toward 127 (spec OQ-7, with Benedikt).
5. Where the challenge repo lives and who holds the protected-module merge rights.

## What this plan deliberately leaves out

The RISC-V metering environment (views and the sanity cycle cap) is not needed for the scored leaderboard and is tracked separately; until it lands, the sanity cap is policed by the review gate (spec section 6). Wallet-vector gating, the presign and cache game clauses, and the trick-template library are full-track work that layers onto the same `SchemeClaim` without changing its shape.
