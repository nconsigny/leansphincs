# WS2–WS4 implementation contract

Status: local review candidate, 2026-09-06. The published spec was updated to v0.13 on 2026-09-07 to carry the signing-failure decision (R8). This document records concrete implementation choices for review, not a change to competition governance.

Harness hardening (2026-09-07): verification now captures submission bytes once,
uses private per-run projects and fresh candidate outputs, and produces
content-bound unranked receipts. The default Linux path replaces the inherited
broad grants with read-only protected/dependency trees, narrowly writable build
outputs, mandatory resource/network restrictions and active boundary probes.
See [HARNESS_SECURITY.md](HARNESS_SECURITY.md) for the precise profile and remaining
production launch gates. The real `SchemeClaim` rejection suite supplements the
metric-only comparator canaries; it does not replace the missing accepted baseline.

Receipt follow-up (2026-09-08): before scoring, the runner now rechecks dependency
pins/cleanliness and tool binaries as well as source/harness integrity. Lake is
included in tool provenance. Complete receipts are atomically published; tests
exercise drift, interruption and write failures without claiming a cryptographic
baseline. No protected Lean interfaces or scoring rules changed.

Termination follow-up (2026-09-09): CLI SIGTERM now enters the same worker cleanup
and interrupted-receipt path as Ctrl-C. Repeated SIGTERM is ignored during
unwinding; library callers' signal handlers are unchanged. Host tests cover a
real process-group cleanup and the named systemd stop request/error path.

Admission follow-up (2026-09-09): the public runner entry point holds a
per-checkout, nonblocking kernel lock before capture through receipt publication.
Contention produces an unranked, retryable `worker_busy` receipt without reading
the candidate. The host suite now has 45 tests. This is cooperative admission,
not a durable queue, aggregate disk quota or crash-surviving cgroup scheduler.

## WS2: oracle and game

`Oracle.lean` pins byte-list inputs and 256-bit outputs, with one lazy random-oracle cache shared by key generation, adaptive adversarial hashing, signing and final verification. Fresh uniform sampling is a separate oracle. A hash input costs `max(1, (length + 31) / 32)` verification units, including domain-separation bytes. Empty and 1–32 byte inputs cost 1; 33–64 cost 2; 96 cost 3. Repeated calls are charged even when the ROM returns a cached answer.

The security budget counts **raw calls across the whole experiment**; it excludes uniform sampling. This follows both reference statements. It is distinct from the score's block-weighted verification budget. This convention admits no adversary below the unavoidable honest-experiment cost; its security interpretation is the work/probability slope, as documented upstream.

`SchemeInterface.lean` fixes messages to 32-byte digests and exposes actual public-key and signature bytes. The submission selects its secret-key type and algorithms. There is no hidden typed signature field, serialization side channel, mutable signing state or epoch parameter. Verification may hash but may not sample random coins. The exact signature-size claim covers every successful output path from every generated key; the verification bound also covers malformed byte strings. Public keys are bounded by 64 bytes.

`Game.lean` records message/optional-signature pairs and excludes only exact successful replays. A new valid signature for an already-signed message wins. Repeated signing requests and requests returning `none` consume the same budget as successful requests for fresh messages. Failures are visible to the adversary and cannot exclude a forgery as replay. `HasSigningQueryBound` imposes at most 2²⁰ requests on every adversarial path for every public key. The shared-ROM hash accounting includes honest signing work.

Following the organizer decision on 2026-09-06, signing returns `Option Bytes`. Two independent claim fields cover correctness and availability: `CorrectOnSuccess` requires probability one of either failure or successful verification; `HasSigningFailureBound S 128` requires `Pr[sign returns none] ≤ 2^-128` for each fixed message, averaged over fresh key generation, signing randomness and their shared ROM. This admits bounded retries without accepting an always-failing signer. It is not a per-key conditional guarantee or adaptive lifetime-availability theorem. The generic bound accepts stronger certificates: `HasSigningFailureBound.mono` transports a 256-bit certificate to the 128-bit gate. The security floor remains 124; availability is a separate theorem, not a scored fourth metric. See `PR19_REVIEW.md` for the remaining baseline proof obligation.

Oracle access is restricted by the type. Arbitrary pure computations are still expressible; the type alone is not a syntactic classifier excluding every non-hash construction. The unconditional ROM theorem and its axiom closure, plus the eventual rule review, enforce the stronger cryptographic restriction.

## WS3: canonical bounds

A `BoundTerm` represents `(numerator / (denominatorPred + 1)) * qH^a * qS^b / 2^k`. Coefficients are non-negative, exponents are natural numbers, and `k` records `n*d` in bits explicitly, so truncated digests are representable without enormous coefficients. Evaluation uses exact rational arithmetic. There is no VCVio, HashSig or game dependency in `Bound.lean`; it uses Mathlib for the convexity proof.

For fixed signing budget and `Q = 2^bits`, `MeetsFloor` checks `B(1) ≤ 1/Q` and `B(Q) ≤ 1`. `MeetsFloor.sound` proves that these checks imply `B(qH) ≤ qH/Q` throughout `[1,Q]`: `B(qH) - qH/Q` is convex. `meetsFloor_iff` proves the converse. This handles constant, linear and higher-degree terms without enumerating 2¹²⁴ budgets. Non-negative coefficients make evaluation at the maximum signing budget conservative for smaller budgets.

`bitSecurity` reports a finite integer, no non-negative floor, or an unbounded result for a zero bound. For a positive `B(1)`, its reduced rational denominator gives a finite search limit. **Acceptance uses the proved `MeetsFloor` predicate directly**, not an off-chain reported bit count. Concrete certificates close with `norm_num [MeetsFloor, evalBound, BoundTerm.weight]`; plain `decide` can get stuck on rational arithmetic's irreducible implementation details.

`idealize` is available for arithmetic experiments. The MVP does not gate on it. Before adopting the full-track idealized rule, fix the normalization of powers of two between coefficients and denominators: `q/2^126` and `4q/2^128` evaluate equally but idealize differently. A syntactic constant-dropping rule needs this additional convention.

`LeanSphincsTest/BoundExamples.lean` checks the 126-bit slope and refined numerical budget from PR #19. These are arithmetic fixtures, not an imported or transported signature-security theorem.

## WS4: claim and comparator

`SchemeClaim S sigma hverify coeffs` bundles correctness on success, the separate 128-bit signing-failure gate, positive scored metrics, exact successful-signature size, public-key size, the worst-case weighted verification bound, a canonical SUF-CMA bound, and the 124-bit endpoint gate. `SchemeClaim.security_le` derives the advertised probability inequality in Lean. The MVP score is the exact integer `sigma * hverify`, with signature size as the tie-break; α = 1.25 belongs to the full competition.

Submissions import `LeanSphincs.Benchmark.Target`, trusted `Mathlib`, `VCVio`, `HashSig` modules, and flat local helpers. Only `.lean` and the three named metric files are admitted. Limits are 1,000 files, 4 MiB per file and 10 MiB total. Source checks reject nested directories, symlinks, dynamic import/elaboration constructs and `native_decide`. The independent verifier must reproduce this policy before opening submissions.

`sigma.txt` and `hverify.txt` contain positive canonical ASCII integers, at most 2⁶³−1. `bound.txt` contains 1–128 JSON arrays `[numerator, denominator, a, b, k]`, with positive reduced fractions, exponents at most 1024, and distinct monomials sorted by `(a,b,k)`. The renderer converts denominators to predecessor encoding after validation; it never inserts arbitrary Lean source from a metric file.

For example, the public 126-bit slope is declared as:

```json
[[4,1,1,0,128]]
```

The renderer imports only the protected target, creates a placeholder `LeanSphincs.Submission.scheme : SigScheme`, and states `LeanSphincs.Benchmark.candidate : SchemeClaim ...` with all three declared values. The comparator's sole `definition_names` entry is that scheme. Every other reachable statement definition must match exactly; candidate proof and scheme axiom closures admit only `propext`, `Classical.choice` and `Quot.sound`.

Comparator is pinned to `777e7f56119efc0fac34003db4efe831e0b53723`, with lean4export pinned by its manifest to `b18d673bd29b476466a51a3be1012df2ed322b10`. The recorded compatibility patch comes from proximity-prize: it kernel-checks untrusted modules with the pinned `leanchecker`, retaining structural comparison and axiom checking. It does not replay the entire trusted library in a fresh kernel environment. Landrun is pinned to `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4`. Ranked deployment still requires a protected verifier image, an external audit and registration.

The comparator canary fixtures are source files under `LeanSphincsTest/Submission/` (`Good`, `WrongSigma`, `WrongMetrics`, `WrongBound`, `SmuggledAxiom`), each defining its own `LeanSphincsTest.Submission.scheme` against the current `Option Bytes` signing interface and proving or (for the axiom case) smuggling `LeanSphincsTest.candidate`. They are built by module name; the `LeanSphincsTest.lean` root deliberately imports only the non-canary test modules. Stale `.olean` files from an older interface were the cause of one kernel-replay failure and are now rebuilt from these sources.

## Provenance and remaining work

- VCVio: `cbd4144b51d92da00dd50f05e068b2348fa6e529`; Lean 4.31.0; transitive revisions in `lake-manifest.json`.
- XMSS statement: leanVM-b `0e82ea922c570b8c4d706a06bc3dc7caf3b34ff0`.
- SPHINCS PR #19: `a1daec3b929d8963b4eee4f1e05985065a96de9d`.
- Harness source policy and comparator patch: proximity-prize `da60d54326afbe85d18a94d0e5c479a724e55ad7`.

WS5 still needs the complete production-profile negative suite, including a real accepted baseline whose declarations can be mutated. WS6 still needs a signature scheme, correctness/serialization and weighted-cost proofs, and a game transport of its security theorem. PR #19 is a concrete additional route to that baseline; it need not wait for the separate HashSig oracle-ization track. Wallet gates, presign/cache semantics, the sanity cycle cap and full-track bound rules remain outside this MVP implementation.
