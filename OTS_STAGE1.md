# Stage 1: hash-graph OTS exploration

Status: experimental implementation, updated 2026-09-10. Not an open competition,
protected OTS claim or security proof. The v0.15 website draft retains the shared
objective for both stages and updates the protected hash-work meter to 64-byte
input units. The legacy MVP claim still has only its original metric fields.
Emile's full SPHINCS reference and ongoing OTS work are not modified here.

## Objective decision

The organizer requests size × keygen × signing × verification, with lower weight
on keygen. Represent that as

`score = signatureBytes * signingWork * verificationWork * keygenWork^beta`

The organizer approved **beta = 1/4** on 2026-09-09. Signing
semantics remain pending: expected work with a separate worst-case cap is
proposed, versus directly scoring worst-case work. Never mix those profiles.
The command defaults to the approved quarter weight; other beta values are
explicitly labelled research overrides. Signing semantics and the declared work
remain required arguments. This weight decision does not freeze the whole profile.

For rational `beta = a/b`, compare the exact rational key
`(signatureBytes * signingWork * verificationWork)^b * keygenWork^a`.
For positive quantities, taking the b-th power preserves the ordering. No
floating-point root or logarithm participates in this comparator.
`LeanSphincs/OTS/Score.lean` defines that key and proves positivity and weak
monotonicity under componentwise cost increases. Its quarter-weight arithmetic
fixtures show that 16× keygen has the same penalty as 2× signature size.
`stage1RankKey` pins the approved quarter-weight specialization.

These metrics are declarations until tied to algorithm certificates. Expected
signing work may be a rational upper bound, but not a measured sample mean.
The probability space, retry bound, charged preprocessing and eventual binding
theorem must be pinned. A separate availability theorem remains required.
Expected signing cost cannot replace the worst-case whole-game security budget.

The organizer approved applying the same four-factor objective to Stage 2 on
2026-09-10. `stage2RankKey` uses the same exact formula; this is not permission to
compare primitives directly with complete schemes, or to mix metric profiles.
The existing legacy full-scheme MVP still scores `sigma * hverify`; its
`SchemeClaim` and three-file contract do not yet certify the new K/S factors.
Website v0.15 is maintained on GitHub, the canonical source by organizer decision
on 2026-09-10. The earlier Claude artifact is a legacy copy, not a synchronized
publication target.

Emile's polynomial-coding annex reinforces the need for full execution metering:
field operations, codebook decoding and preprocessing are not free under a cycle
profile. Keep the hash-work view and add the cycle-based four-factor view; enforce
hard execution/memory gates before promotion. The definitive prize profile,
weights and caps remain to calibrate. The existing 45 s / 1.5 s wallet budgets
have not been replaced by the illustrative 5 minute / 5 second thresholds.
See [POLYNOMIAL_CODING_REVIEW.md](POLYNOMIAL_CODING_REVIEW.md).

At fixed signature size and signing budget, the conditional objective can be
minimum verification work. Hash chains are not presumed optimal: the organizer
reports regimes where Reed–Solomon-coded candidates improve this tradeoff.
Keep such conditional frontiers without claiming a global lower bound or dropping
keygen/availability gates. The current four fixed-family experiments do not yet
implement the annex's complete coded signer/verifier.

## Implemented foundations

- `LeanSphincs/OTS/Graph.lean`: finite acyclic-dependency predicate, distinct gate
  addresses, source/output vertices, structural reconstruction predicate and
  costs using the existing protected `hashWeight`. Each query returns two 128-bit
  vertices from the 256-bit oracle; using only one output does not reduce cost.
  A theorem bounds once-per-gate subset cost by total graph keygen cost.
- `LeanSphincsTest/OTSGraph.lean`: reconstruction/missing-input/cycle and input
  charging fixtures. The graph predicate does not enforce disclosure minimality,
  incomparability, or a byte-level verifier implementation. A reconstruction
  schedule still needs a root-correctness theorem against key generation.
- `LeanSphincs/OTS/Evaluate.lean`: actual `OracleComp HashSpec` evaluation of
  schedules, with fixed 16-byte little-endian addresses and values. Proved byte
  encoding injectivity, address separation, exact input length, gate query weight
  and worst-case weighted schedule query bound on every oracle response path.
  Missing inputs fail before hashing; repeats are charged repeatedly. For
  duplicate-free schedules, the operational budget equals the gate-subset cost
  and is at most graph keygen cost. This does not yet prove root correctness,
  randomized key generation or a complete OTS verifier bound including encoding.
- `LeanSphincs/OTS/Reconstruct.lean`: the actual oracle computation reconstructs
  the reference root when the disclosed values agree with an oracle-consistent
  assignment. This uses VCVio's `evalWithAnswerFn`, not a separate mock evaluator.
  Constructing the assignment from randomized keygen and transporting the result
  through the shared lazy ROM remain to prove.
- `LeanSphincs/OTS/Failure.lean`: real-valued adaptive survival-envelope theorem,
  an exception-aware variant for cached/bad steps, and a conservative exact
  retry bound at per-step success 2^-16. The actual signer must still establish
  the step premise and any exception allowance; these are not assumed facts.
- `scripts/ots_experiments.py`: exact integer polynomial counting for the four
  fixed graph shapes in *looking for the optimal hash-based one-time signature*.
  It searches reconstruction-cost layers and disclosure-size caps, selects the
  product-minimizing pair within each graph, and optionally emits each graph's
  size/verification Pareto frontier. Keygen is fixed per graph and the explicit
  signing metric is common across these codebooks. This is not exhaustive graph
  synthesis or a global optimality result.
- `scripts/check-ots-axioms.lean`: audit every declaration under `LeanSphincs.OTS`,
  including generated/private declarations, against the three standard axioms.
  Experimental modules are not imported by the protected MVP Target.

## Reproducible experiments

```sh
python3 scripts/ots_experiments.py --profile rom32-input64 --beta 1/4 \
  --signing-work 131072 --signing-kind expected-upper-bound --include-frontier
python3 -m unittest discover -s tests -v
lake build LeanSphincsTest
lake env lean scripts/check-ots-axioms.lean
```

The example signing metric is hypothetical: 2^16 expected encoding queries times
two weighted units per query under the assumed layout. It is not a proved
signing certificate. The output explicitly says `ranked: false`,
`security_proved: false`, and `costs_certified: false`.

`paper` reproduces the note's 73/68/63/60 verification-cost minima under its own
oracle. The current `rom32-input64` profile assumes a fixed 16-byte unique gate
address encoded in every input, in addition to the 16-byte values. The oracle
output stays 32 bytes, while work is `ceil(inputBytes / 64)`. A four-input merge
or a 32-byte message plus 32-byte nonce costs two units with the address included.
A four-output expansion uses two separately addressed 32-byte-output queries.
Address serialization and separation are proved for the evaluator; reserved
encoding domains, construction-specific graph translation and simulation
equivalence still need proofs. Empty input costs zero hash-work units but still
counts as a security query; these graph queries all contain nonempty addresses.
The historical `rom32` profile keeps its old 32-byte input-unit costs for
reproduction only. JSON reports distinguish the meters; do not mix their scores.
These are candidate-layout choices, not a new competition oracle definition.

Under this layout, with 2^112 disclosures required and a cap of 128 disclosed
values, the product-selected points for the fixed graph shapes are:

| Fixed shape | Signature bytes | Keygen | Verification |
| --- | ---: | ---: | ---: |
| Chains | 1888 | 169 | 75 |
| Branching forest | 1648 | 201 | 96 |
| Pairwise shared seeds | 1744 | 220 | 101 |
| Four-way shared seeds | 1824 | 329 | 123 |

All rows use the same stipulated signing work; the CLI computes the four-factor
rank key for the supplied beta. These shapes no longer meet the note's keygen
budget of 168 under this meter. That budget is not adopted as a Stage 1 rule.
This reversal is not a general impossibility result for branching/shared seeds.

Size is a proposed canonical padded length: for each cost layer, retain eligible
disclosures in increasing size and a deterministic within-size order until there
are enough. Pad to the chosen cap and reject noncanonical padding. The counting
code does not implement the decoder or prove this SUF-preserving serialization.

## Next proof milestones, in order

1. Beta = 1/4 is approved. Agree signing semantics and pin hard signing/keygen
   budgets separately.
2. Address serialization and actual oracle evaluation/metering are implemented.
   Reconstruction against an oracle-consistent reference is now proved. Next
   construct that reference from randomized keygen and transport through the ROM; instantiate each
   searched graph and bind its counting model to the actual implementation.
3. Formalize codebook counting/unranking, minimality and incomparability, including
   shared-seed disclosures. Prove canonical encoding and exact signature length.
4. Prove correctness and the fixed-message signing-failure certificate, plus the
   selected signing cost certificate. Include failed attempts and preprocessing.
5. With Emile, pin standalone chosen-message OTS versus the internal-root game.
   Prove strong one-time security under that game, with our raw whole-experiment
   query budget; combinatorial incomparability alone is not that theorem.
6. Add multi-instance and same-message repeat-signing contracts before composition.
   Only then add a protected OTS claim/comparator and an accepted baseline with
   mutated negative tests. Preserve an open non-template submission route.

No wallet feasibility, 127-bit theorem, certified candidate or optimal primitive
is inferred from these arithmetic and graph foundations.

## Worst-case failure probability

The organizer requested explicit treatment of worst-case probability. This does
not by itself decide whether the signing score should be expected or worst-case
work; that separate choice remains pending.

The new proof bounds survival mass from a step inequality
`tail(n+1) <= tail(n)*(1-p)`. A success lower bound conditional on every surviving
history is sufficient, without independence. At `p = 2^-16`, blocks of 65536
attempts reduce the proved envelope by at least half. Hence:

| Illustrative target | Attempts | Worst-case encoding units at 3/attempt |
| --- | ---: | ---: |
| Single-request failure <= 2^-128 | 8,388,608 | 25,165,824 |
| Single-request failure <= 2^-256 | 16,777,216 | 50,331,648 |
| Per-request 2^-148, for a 2^20-request union bound of 2^-128 | 9,699,328 | 29,097,984 |

These are conservative sufficient caps **conditional on the step premise**, not
chosen protocol caps or completed availability certificates. The third row is a
composition illustration, not a change from the one-request OTS security game.
Only encoding queries are included in those work totals.

Freshness must be proved in the real game. Distinct signer nonces do not establish
that an adversary has never queried the corresponding inputs. A worst case over
adversary strategies with probability over the ROM is also different from
conditioning on every possible, including arbitrarily unlikely, oracle history.
Do not assert a uniform success probability for cached answers.

The exception-aware theorem instead accepts
`tail(n+1) <= tail(n)*(1-p) + bad(n)` and concludes the geometric bound plus
`sum bad(n)`. To certify a final 2^-128 failure gate, **both terms together** must
fit it. For example, allocating 2^-129 to each term suffices; neither exception
probability nor the uniform fresh-answer premise may be dropped.

Before eligibility, define the precise worst-case request/history scope, prove
the cache/freshness and retry behavior against the actual signer, and transport
the bound to the protected availability game. The current MVP fixed-message,
fresh-key availability clause has not been silently strengthened or replaced.

Validation on 2026-09-09: 53 host tests passed; `lake build LeanSphincs
LeanSphincsTest` completed successfully (3305 jobs); both the protected and OTS
axiom audits admitted only standard axioms. No OTS security claim was added.

Quarter-weight/evaluator follow-up: 54 host tests pass; the complete library/test
build passes (3307 jobs), including byte injectivity, address separation,
missing-input rejection, both 128-bit output halves, repeated-gate charging and
the actual weighted-query theorem. Both axiom audits pass. The quarter-weight
CLI default is covered by a regression that also checks the unranked/unproved flags.

Reconstruction/failure follow-up: 54 host tests pass; full Lean build passes
(3311 jobs); both axiom audits pass. Lean fixtures cover correct reconstruction,
reversed invalid schedules, incorrect disclosures/reference assignments, 128/256-bit
failure envelopes, explicit exception accounting and single-request/lifetime arithmetic.
