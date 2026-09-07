# Third-party source notices

`scripts/check-submission-imports.sh` is adapted from proximity-prize/proximity-prize at `da60d54326afbe85d18a94d0e5c479a724e55ad7` (Apache-2.0). Changes replace the challenge names, admitted metric files and library prefixes, and forbid native_decide. `benchmark/comparator-leanchecker.patch` is the compatibility patch from that harness, with expanded diff context. See `licenses/Apache-2.0.txt`.

The downloaded comparator and lean4export retain their own source headers and licenses in `.benchmark-tools/`. VCVio, Mathlib and the other locked dependencies retain their licenses in their Lake packages. Game design follows the public leanVM-b XMSS/SPHINCS statements cited in IMPLEMENTATION.md; no upstream scheme proof is bundled as an accepted submission.
