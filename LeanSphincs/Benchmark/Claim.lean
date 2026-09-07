import LeanSphincs.Benchmark.Game
import LeanSphincs.Benchmark.Bound

/-! Protected MVP claim. Full-track idealized/decay, wallet, presign/cache and
cycle-cap clauses are intentionally not represented as completed MVP gates. -/

namespace LeanSphincs.Benchmark

open ENNReal

def signingBudget : Nat := 2 ^ 20
def securityFloor : Nat := 124
def signingFailureBits : Nat := 128

noncomputable def boundProbability (coeffs : BoundCoeffs) (qH qS : Nat) : ℝ≥0∞ :=
  ENNReal.ofReal (evalBound coeffs qH qS : ℝ)

structure SchemeClaim (S : SigScheme) (sigmaBytes hVerify : Nat) (coeffs : BoundCoeffs) : Prop where
  correct : CorrectOnSuccess S
  signing_failure : HasSigningFailureBound S signingFailureBits
  sigma_positive : 0 < sigmaBytes
  sigma_size : HasSignatureSize S sigmaBytes
  public_key_size : HasPublicKeySize S 64
  hverify_positive : 0 < hVerify
  verify_queries : HasVerificationBound S hVerify
  security : ∀ (A : Adversary) (qH : Nat),
    HasHashQueryBound S A qH → HasSigningQueryBound A signingBudget →
      sufAdvantage S A ≤ boundProbability coeffs qH signingBudget
  floor : MeetsFloor coeffs signingBudget securityFloor

/-- The certified canonical bound entails the advertised 124-bit inequality
throughout the nonzero budget range, with no off-chain numerical assumption. -/
theorem SchemeClaim.security_le {S : SigScheme} {sigma hverify : Nat} {coeffs : BoundCoeffs}
    (claim : SchemeClaim S sigma hverify coeffs) (A : Adversary) (qH : Nat)
    (hlo : 1 ≤ qH) (hhi : qH ≤ 2 ^ securityFloor)
    (hH : HasHashQueryBound S A qH) (hS : HasSigningQueryBound A signingBudget) :
    sufAdvantage S A ≤ (qH : ℝ≥0∞) / 2 ^ securityFloor := by
  have hq : evalBound coeffs qH signingBudget ≤ (qH : ℚ) / 2 ^ securityFloor :=
    claim.floor.sound (by exact_mod_cast hlo) (by exact_mod_cast hhi)
  have hr : (evalBound coeffs qH signingBudget : ℝ) ≤ (qH : ℝ) / 2 ^ securityFloor := by
    have hc := (Rat.cast_le (K := ℝ)).mpr hq
    simpa only [Rat.cast_div, Rat.cast_natCast, Rat.cast_pow, Rat.cast_ofNat] using hc
  apply (claim.security A qH hH hS).trans
  have := ENNReal.ofReal_le_ofReal hr
  simpa [boundProbability, ENNReal.ofReal_div_of_pos (by positivity : (0 : ℝ) < 2 ^ securityFloor),
    ENNReal.ofReal_pow (by norm_num : (0 : ℝ) ≤ 2)] using this

end LeanSphincs.Benchmark
