import Mathlib.Analysis.Convex.Mul
import Mathlib.Analysis.Convex.Jensen
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Linarith

/-! Exact rational canonical bounds, independent of the scheme and VCVio.
The denominator exponent records n*d in bits, including truncated digests.
Non-negative rational coefficients make B
convex in qH, so the bit floor reduces exactly to two endpoint inequalities. -/

namespace LeanSphincs.Benchmark

structure BoundTerm where
  numerator : Nat
  denominatorPred : Nat
  hashExponent : Nat
  signExponent : Nat
  denominatorBits : Nat
deriving DecidableEq, Repr

abbrev BoundCoeffs := List BoundTerm

def BoundTerm.weight (t : BoundTerm) (qS : Nat) : ℚ :=
  (t.numerator : ℚ) / (t.denominatorPred + 1) * (qS : ℚ) ^ t.signExponent /
    2 ^ t.denominatorBits

def evalBound : BoundCoeffs → ℚ → Nat → ℚ
  | [], _, _ => 0
  | t :: ts, qH, qS => t.weight qS * qH ^ t.hashExponent + evalBound ts qH qS

def idealize (coeffs : BoundCoeffs) : BoundCoeffs :=
  coeffs.map fun t => { t with numerator := 1, denominatorPred := 0 }

/-- Exact endpoint test for B(qH,qS) ≤ qH / 2^bits throughout [1,2^bits]. -/
def MeetsFloor (coeffs : BoundCoeffs) (qS bits : Nat) : Prop :=
  evalBound coeffs 1 qS ≤ 1 / (2 : ℚ) ^ bits ∧
    evalBound coeffs ((2 : ℚ) ^ bits) qS ≤ 1

instance (coeffs : BoundCoeffs) (qS bits : Nat) : Decidable (MeetsFloor coeffs qS bits) :=
  inferInstanceAs (Decidable (_ ∧ _))

theorem weight_nonneg (t : BoundTerm) (qS : Nat) : 0 ≤ t.weight qS := by
  unfold BoundTerm.weight
  positivity

theorem evalBound_nonneg (coeffs : BoundCoeffs) {qH : ℚ} (h : 0 ≤ qH) (qS : Nat) :
    0 ≤ evalBound coeffs qH qS := by
  induction coeffs with
  | nil => simp [evalBound]
  | cons t ts ih =>
    exact add_nonneg (mul_nonneg (weight_nonneg t qS) (pow_nonneg h _)) ih

theorem evalBound_convex (coeffs : BoundCoeffs) (qS : Nat) :
    ConvexOn ℚ (Set.Ici 0) (fun qH => evalBound coeffs qH qS) := by
  induction coeffs with
  | nil => exact convexOn_const 0 (convex_Ici 0)
  | cons t ts ih =>
    exact ((convexOn_pow t.hashExponent).smul (weight_nonneg t qS)).add ih

/-- Soundness of the fast, decidable gate, including hash-independent terms. -/
theorem MeetsFloor.sound {coeffs : BoundCoeffs} {qS bits : Nat}
    (h : MeetsFloor coeffs qS bits) {qH : ℚ}
    (hlo : 1 ≤ qH) (hhi : qH ≤ 2 ^ bits) :
    evalBound coeffs qH qS ≤ qH / 2 ^ bits := by
  have hpow : (0 : ℚ) < 2 ^ bits := by positivity
  have linear : ConcaveOn ℚ (Set.Ici 0) (fun x : ℚ => x / 2 ^ bits) := by
    simpa [smul_eq_mul, div_eq_mul_inv, mul_comm] using
      (concaveOn_id (convex_Ici (0 : ℚ))).smul (le_of_lt (inv_pos.mpr hpow))
  have hc := (evalBound_convex coeffs qS).sub linear
  have hm := hc.le_max_of_mem_Icc (show (0 : ℚ) ≤ 1 by norm_num)
    (le_of_lt hpow) (show qH ∈ Set.Icc 1 (2 ^ bits) from ⟨hlo, hhi⟩)
  have hend : evalBound coeffs (2 ^ bits) qS - (2 : ℚ) ^ bits / 2 ^ bits ≤ 0 := by
    rw [div_self (ne_of_gt hpow)]
    exact sub_nonpos.mpr h.2
  exact sub_nonpos.mp (hm.trans (max_le (sub_nonpos.mpr h.1) hend))

theorem meetsFloor_iff (coeffs : BoundCoeffs) (qS bits : Nat) :
    MeetsFloor coeffs qS bits ↔
      ∀ qH : ℚ, 1 ≤ qH → qH ≤ 2 ^ bits → evalBound coeffs qH qS ≤ qH / 2 ^ bits := by
  constructor
  · exact fun h _ hlo hhi => h.sound hlo hhi
  · intro h
    have hp : (1 : ℚ) ≤ 2 ^ bits := one_le_pow₀ (by norm_num)
    refine ⟨h 1 le_rfl hp, ?_⟩
    simpa using h (2 ^ bits) hp le_rfl

/-- Reporting distinguishes no non-negative floor from the identically-zero
bound, which has no largest finite security level. -/
inductive SecurityBits where
  | belowZero
  | finite (bits : Nat)
  | unbounded
deriving DecidableEq, Repr

/-- Scan a finite exact range. For positive B(1), its reduced denominator D
gives B(1) ≥ 1/D; hence a passing bit level cannot exceed log₂(D).
The acceptance predicate is `MeetsFloor`, whose soundness is proved above. -/
def bitSecurity (coeffs : BoundCoeffs) (qS : Nat) : SecurityBits :=
  if evalBound coeffs 1 qS = 0 then .unbounded
  else if ¬ MeetsFloor coeffs qS 0 then .belowZero
  else .finite ((List.range ((evalBound coeffs 1 qS).den.log2 + 1)).foldl
    (fun best bits => if MeetsFloor coeffs qS bits then max best bits else best) 0)

#guard evalBound [⟨3, 1, 2, 1, 0⟩] 2 4 = 24
#guard MeetsFloor [⟨1, 0, 2, 0, 256⟩] (2^20) 128
#guard ¬ MeetsFloor [⟨1, 0, 2, 0, 256⟩] (2^20) 129
#guard MeetsFloor [⟨256, 0, 2, 0, 256⟩] (2^20) 124
#guard ¬ MeetsFloor [⟨257, 0, 2, 0, 256⟩] (2^20) 124
#guard ¬ MeetsFloor [⟨1, 0, 0, 0, 0⟩] (2^20) 124
#guard bitSecurity [] 0 = .unbounded
#guard bitSecurity [⟨2, 0, 0, 0, 0⟩] 0 = .belowZero
#guard bitSecurity [⟨1, 0, 2, 0, 256⟩] (2^20) = .finite 128
#guard bitSecurity (idealize [⟨256, 0, 2, 0, 256⟩]) (2^20) = .finite 128
#guard bitSecurity [⟨1, 0, 1, 0, 128⟩] (2^20) = .finite 128

end LeanSphincs.Benchmark
