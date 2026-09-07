import VCVio.OracleComp.QueryTracking.RandomOracle.Simulation
import VCVio.OracleComp.QueryTracking.QueryBound

/-! The protected MVP oracle and the distinct security and scoring meters. -/

open OracleComp OracleSpec

namespace LeanSphincs.Benchmark

abbrev Bytes := List UInt8
abbrev HashOutput := BitVec 256
abbrev HashSpec := Bytes →ₒ HashOutput
abbrev OracleWorld := unifSpec + HashSpec

/-- One unit per started 32-byte input block; even an empty query costs one.
All input bytes, including domain separation and length encoding, are charged. -/
def hashWeight (input : Bytes) : Nat := max 1 ((input.length + 31) / 32)

/-- A worst-case structural bound, on every response path, including repeats. -/
def HasVerifyCost {α : Type} (comp : OracleComp HashSpec α) (budget : Nat) : Prop :=
  comp.IsQueryBound budget (fun input remaining => hashWeight input ≤ remaining)
    (fun input remaining => remaining - hashWeight input)

theorem HasVerifyCost.pure {α : Type} (x : α) (budget : Nat) :
    HasVerifyCost (pure x) budget := isQueryBound_pure x budget _ _

theorem HasVerifyCost.bind {α β : Type} {comp : OracleComp HashSpec α}
    {next : α → OracleComp HashSpec β} {first rest : Nat}
    (hfirst : HasVerifyCost comp first) (hrest : ∀ x, HasVerifyCost (next x) rest) :
    HasVerifyCost (comp >>= next) (first + rest) := by
  apply isQueryBound_bind (· + ·) (h₁ := hfirst) (h₂ := hrest)
  · intro input b₁ b₂ b h
    constructor <;> omega
  · intro input b₁ b₂ b h
    constructor <;> omega

theorem hasVerifyCost_query_iff (input : Bytes) (budget : Nat) :
    HasVerifyCost (liftM (HashSpec.query input)) budget ↔ hashWeight input ≤ budget :=
  isQueryBound_query_iff input budget _ _

/-- Sampling is private fresh randomness. Hash answers are lazy, uniform and
consistent, with one cache shared by every stage of the experiment. -/
noncomputable def romImpl : QueryImpl OracleWorld (StateT (QueryCache HashSpec) ProbComp) :=
  unifFwdImpl HashSpec +
    (randomOracle : QueryImpl HashSpec (StateT (QueryCache HashSpec) ProbComp))

noncomputable def runROM {α : Type} (comp : OracleComp OracleWorld α) : ProbComp α :=
  (simulateQ romImpl comp).run' ∅

#guard hashWeight [] = 1
#guard hashWeight (List.replicate 1 0) = 1
#guard hashWeight (List.replicate 32 0) = 1
#guard hashWeight (List.replicate 33 0) = 2
#guard hashWeight (List.replicate 64 0) = 2
#guard hashWeight (List.replicate 96 0) = 3

end LeanSphincs.Benchmark
