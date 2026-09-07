# MVP submission contract

Status: implementer guide for the staged harness, not an announcement that
submissions or prizes are open. The published competition spec remains v0.12.

## Package

Provide a flat folder containing:

```text
Scheme.lean      algorithms against the protected oracle interface
Solution.lean    the exported SchemeClaim proof
sigma.txt       exact successful-signature byte length
hverify.txt     worst-case block-weighted verification bound
bound.txt       canonical security-bound coefficients
Helper.lean     optional; additional flat Lean helper modules are allowed
```

Use UTF-8 source, with filenames matching `[A-Za-z_][A-Za-z0-9_]*.lean`.
No build files, compiled artifacts, symlinks, subdirectories or executable tools
are admitted. The limits are 1,000 files, 4 MiB per file and 10 MiB total.

`Scheme.lean` imports `LeanSphincs.Benchmark.Target` and defines
`LeanSphincs.Submission.scheme : LeanSphincs.Benchmark.SigScheme`.
Local helpers are imported as `LeanSphincs.Submission.Helper`.
`Solution.lean` exports exactly `LeanSphincs.Benchmark.candidate` with type:

```lean
LeanSphincs.Benchmark.SchemeClaim LeanSphincs.Submission.scheme
  sigmaBytes hVerify coeffs
```

Only the scheme definition is a comparator hole. The oracle, game, claim fields,
budgets, metric arguments and bound semantics must match the protected statement.
Permitted imports are the protected `Target`, pinned Mathlib/VCVio/HashSig, and
flat local helpers. Use one import per line in the initial import block. Custom
elaborators/macros, native_decide, build-time execution and kernel-bypass features
are rejected. All theorem/algorithm axiom closures must stay within `propext`,
`Classical.choice` and `Quot.sound`; `sorry` is not admitted.

## Proof obligations

- Correctness on success and, separately, signing failure probability ≤ 2⁻¹²⁸
  for every fixed 32-byte message under fresh key generation and a shared ROM.
  Signing returns `Option Bytes`; a stronger 2⁻²⁵⁶ certificate also qualifies.
- Exact positive signature size for every successful output, public-key size
  ≤ 64 bytes, and a positive verification bound covering malformed inputs too.
- A canonical SUF-CMA bound for every admissible adversary, with at most 2²⁰
  signing requests, and the protected 124-bit endpoint predicate.

Failed signing responses are visible and count against the signing-query budget.
Only an exact successful message/signature pair is a replay. Security counts raw
hash queries across the whole experiment; verification scoring instead charges
`max(1, ceil(inputBytes / 32))` per call, including domain-separation bytes. This
block convention remains staged for organizer review before freeze.

## Declared metrics

`sigma.txt` and `hverify.txt` each contain one positive ASCII decimal integer
(≤ 2⁶³−1), without leading zeros or whitespace other than an optional final LF.
`bound.txt` is a JSON array of 1–128 terms:

```json
[[4,1,1,0,128]]
```

Each term `[numerator, denominator, a, b, k]` denotes
`(numerator / denominator) * qH^a * qS^b / 2^k`. Fractions must be positive and
reduced; exponents are natural numbers ≤ 1024; terms are unique and sorted by
`(a,b,k)`. In Lean, the example is `[⟨4, 0, 1, 0, 128⟩]` because the denominator
uses predecessor encoding. It represents the 126-bit slope, but declaring it is
not a proof that your scheme satisfies it.

The MVP score is the exact integer `sigma * hverify`, minimized, with signature
size as the tie-break. No fourth scored file is needed for signing availability.

## Local verification

```sh
bash setup.sh
bash benchmark.sh /absolute/path/to/submission
```

The final line points to a retained `result.json`, captured inputs and logs.
Editing the original folder after capture does not change what was verified.
Each run has fresh candidate build outputs. An `accepted` local result is still
unranked: no remote verifier has registered, audited or promoted it.

If sandbox setup fails, fix the host using [HARNESS_SECURITY.md](HARNESS_SECURITY.md).
Do not treat the explicit `--insecure-local` option as a substitute for the
competition verifier; it is for organizer-owned diagnostics only.

No complete accepted example is provided yet. The metric canaries are deliberately
not security proofs. Baseline #0 is the next end-to-end cryptographic deliverable.
