import Mathlib.Tactic

/-! Experimental four-factor objective for both research stages.
Not imported by the protected MVP Target.
Metrics still need certificates binding them to an actual scheme. -/

namespace LeanSphincs.OTS

structure Costs where
  signatureBytes : ℚ
  keygen : ℚ
  signing : ℚ
  verification : ℚ
deriving DecidableEq, Repr

def Costs.Positive (c : Costs) : Prop :=
  0 < c.signatureBytes ∧ 0 < c.keygen ∧ 0 < c.signing ∧ 0 < c.verification

/-- For β = a/b, compare the b-th power of σ * S * V * K^β.
This avoids floating-point roots. Organizers must pin 0 < a < b.
Signing semantics (expected or worst-case) belong to the profile, not this formula. -/
def rankKey (a b : Nat) (c : Costs) : ℚ :=
  (c.signatureBytes * c.signing * c.verification) ^ b * c.keygen ^ a

def Costs.DominatedBy (c d : Costs) : Prop :=
  c.signatureBytes ≤ d.signatureBytes ∧ c.keygen ≤ d.keygen ∧
    c.signing ≤ d.signing ∧ c.verification ≤ d.verification

theorem rankKey_pos (a b : Nat) (c : Costs) (h : c.Positive) :
    0 < rankKey a b c := by
  rcases h with ⟨hs, hk, hg, hv⟩
  unfold rankKey
  positivity

/-- No Pareto-dominated metric vector can have a better rank key. -/
theorem rankKey_mono (a b : Nat) (c d : Costs) (hc : c.Positive)
    (h : c.DominatedBy d) : rankKey a b c ≤ rankKey a b d := by
  rcases hc with ⟨hs, hk, hg, hv⟩
  rcases h with ⟨hsd, hkd, hgd, hvd⟩
  have hds : 0 < d.signatureBytes := lt_of_lt_of_le hs hsd
  have hdg : 0 < d.signing := lt_of_lt_of_le hg hgd
  have hdv : 0 < d.verification := lt_of_lt_of_le hv hvd
  unfold rankKey
  gcongr

/-- Quarter-weight specialization approved for Stage 1 on 2026-09-09. -/
theorem quarterKey (c : Costs) :
    rankKey 1 4 c = (c.signatureBytes * c.signing * c.verification)^4 * c.keygen := by
  simp [rankKey]

/-- The approved Stage 1 ranking key. Signing semantics still require a profile. -/
def stage1RankKey (c : Costs) : ℚ := rankKey 1 4 c

/-- The same formula for complete schemes, approved 2026-09-10. Stage-specific
game and metric certificates are still required; stages are not cross-ranked. -/
def stage2RankKey (c : Costs) : ℚ := rankKey 1 4 c

theorem stage2RankKey_eq_stage1 (c : Costs) : stage2RankKey c = stage1RankKey c := rfl

end LeanSphincs.OTS
