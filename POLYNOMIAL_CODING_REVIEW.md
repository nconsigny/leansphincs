# Polynomial-coded OTS: implications for the competition

Source: the organizer-supplied September 9 messages and image of annex A,
“Polynomial coding”. Only that displayed page is reviewed here; the complete
signing/decoding algorithm and security proof were not provided. The prior
six-page note and [Top of the Hypercube](https://eprint.iacr.org/2025/889) are
context, not interchangeable security results for this new construction.

## What the displayed construction does

It uses 64 independent 136-bit seeds. A 512-bit hash output supplies 64 byte-sized
coefficients per column of a degree-at-most-63 polynomial over GF(256). Evaluating
at all 256 field elements gives a 256-by-64 byte table. Each 64-byte row is hashed
to a 128-bit digest; a four-ary Merkle tree of height four authenticates the 256
row digests. The public key is the root. Its abstract keygen count is
`64 + 256 + (64 + 16 + 4 + 1) = 405` calls.

The illustration reveals eight seeds, supplies the other 56 entries for each
opened row, and describes 56 tree-proof digests. It does not specify the complete
row-selection codebook or verifier, so no full signing/verification score or
strong-unforgeability claim is derived from it here.

## The cost-model warning is real

The annex allows a 64-byte output per call and free field arithmetic. Our oracle
returns 32 bytes and charges all supplied input bytes. Under the **assumed**
16-byte address layout used by the current OTS experiments:

| Keygen operation | Assumed implementation | Weighted units |
| --- | --- | ---: |
| 64 coefficient expansions | two calls per 17-byte seed; 33-byte tagged input | 256 |
| 256 row hashes | 80-byte tagged inputs | 768 |
| 85 Merkle parents | 80-byte tagged inputs | 255 |
| Total | same displayed shape, not re-optimized | 1,279 |

This is a source-level re-metering, not a Lean cost certificate or a practical
hash instantiation. A concrete layout, domain-separation/simulation proof and
re-optimization may change it. It is not comparable to a full SPHINCS score.

Naive Horner evaluation of all columns at all points uses
`64 * 256 * 63 = 1,032,192` GF(256) multiplications and the same number of additions.
Faster multipoint evaluation or other algorithms may reduce that. These counts
are **not** RISC-V cycles; neither field operations nor codebook unranking may be
omitted from the execution profile. The raw table alone occupies 16,384 bytes,
before seeds, coefficients, tree nodes, decoder tables and scratch memory.

Reproduce these limited arithmetic checks:

```sh
python3 scripts/polynomial_annex.py
python3 -m unittest discover -s tests -v
```

## Security and template implications

- Public polynomial/field arithmetic adds no hardness assumption by itself.
  Do not reject a construction merely for using Reed–Solomon coding; require its
  actual ROM security proof and full-program resource accounting.
- The 256 evaluations are correlated. Any 64 distinct evaluations determine a
  degree-at-most-63 column polynomial. This is a boundary the leakage proof must
  handle, not a demonstrated attack on this OTS. Multiple exposures/composition
  cannot be justified by counting hash-graph cuts alone.
- Hash-derived coefficients are not 64 independently sampled secret bytes in
  the implemented key: the seed/oracle relation must stay in the security game.
- The existing optional graph DSL has 128-bit vertices and direct hash gates.
  It does not yet represent 8-bit coded entries, 136-bit seeds, or deterministic
  field-operation nodes. Do not shoehorn the annex into it and inherit its
  incomparability/counting assumptions. An extended typed circuit model needs
  correctness, leakage and instruction-cost proofs; direct pure-ROM scheme
  submissions must remain an alternative to templates.

## Decisions applied on 2026-09-10

Both stages use `size * signing * verification * keygen^(1/4)`. This formula may
be instantiated with separately identified hash-work and execution-cost profiles.
Do not mix units or expected/worst-case signing semantics on one board. Preserve
the full frontier; do not proclaim the hash-minimal shape a practical winner.

Hard keygen/signing latency, verification execution and memory gates remain
required for promotion. Keep the existing 45-second keygen / 1.5-second signing
wallet budgets pending an explicit replacement decision. Their implementation
and the cycle profile remain launch work. The final award profile and expected-
versus-worst-case signing score remain open; worst-case failure probability is
a separate proof obligation.

No cryptographic interface, audited upstream pin or protected legacy claim was
changed to accommodate an unproved candidate. The next execution work is a
metered encoding kernel plus exact oracle/program binding, not an aesthetic ban
on unusual constructions or a silent switch to a different hash oracle.
