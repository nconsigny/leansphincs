import LeanSphincs.OTS.Score

open LeanSphincs.OTS

example : stage1RankKey ⟨2, 16, 3, 5⟩ = 12960000 := by
  norm_num [stage1RankKey, rankKey]

example : stage2RankKey ⟨2, 16, 3, 5⟩ = 12960000 := by
  norm_num [stage2RankKey, rankKey]

example : rankKey 1 4 ⟨2, 16, 3, 5⟩ = 12960000 := by
  norm_num [rankKey]

/-- A 16-fold keygen increase has the same quarter-weight penalty as doubling
signature size, with the other metrics held fixed. -/
example : rankKey 1 4 ⟨2, 16, 3, 5⟩ = rankKey 1 4 ⟨4, 1, 3, 5⟩ := by
  norm_num [rankKey]

example : rankKey 1 4 ⟨2, 1, 3, 5⟩ < rankKey 1 4 ⟨2, 1, 4, 5⟩ := by
  norm_num [rankKey]
