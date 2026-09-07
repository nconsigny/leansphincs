import LeanSphincs.Benchmark.Oracle

/-! Byte-level scheme interface. Public inputs and signatures have no hidden
typed fields; verification is deterministic apart from its hash oracle. -/

open OracleComp OracleSpec ENNReal

namespace LeanSphincs.Benchmark

/-- Messages are fixed 32-byte execution-layer digests. -/
abbrev Message := BitVec 256

/-- The only submission-supplied algorithm bundle. Signing has no mutable state
argument or output. Key generation and signing may sample fresh randomness.
Public keys and signatures are the actual wire bytes used in the game. -/
structure SigScheme where
  SecretKey : Type
  keygen : OracleComp OracleWorld (Bytes × SecretKey)
  sign : SecretKey → Message → OracleComp OracleWorld (Option Bytes)
  verify : Bytes → Message → Bytes → OracleComp HashSpec Bool

def correctnessExperiment (S : SigScheme) (message : Message) : OracleComp OracleWorld Bool := do
  let (pk, sk) ← S.keygen
  match ← S.sign sk message with
  | none => return true
  | some signature => liftM (S.verify pk message signature)

/-- No successful signature is invalid, with probability one in the fresh
key-generation/signing experiment under a shared ROM. Failure is checked
separately by `HasSigningFailureBound`, so this clause alone is vacuous for
an always-failing signer. -/
def CorrectOnSuccess (S : SigScheme) : Prop :=
  ∀ message, Pr[= true | runROM (correctnessExperiment S message)] = 1

def signingFailureExperiment (S : SigScheme) (message : Message) :
    OracleComp OracleWorld Bool := do
  let (_, sk) ← S.keygen
  return (← S.sign sk message).isNone

/-- Availability for each fixed message, averaged over fresh key generation,
signing randomness and their shared ROM. This is not a conditional guarantee
for every key or an adaptive lifetime-availability claim. -/
def HasSigningFailureBound (S : SigScheme) (bits : Nat) : Prop :=
  ∀ message, Pr[= true | runROM (signingFailureExperiment S message)] ≤
    1 / (2 : ℝ≥0∞) ^ bits

/-- A stronger availability certificate also meets any weaker bit threshold. -/
theorem HasSigningFailureBound.mono {S : SigScheme} {weaker stronger : Nat}
    (h : HasSigningFailureBound S stronger) (hle : weaker ≤ stronger) :
    HasSigningFailureBound S weaker := by
  intro message
  apply (h message).trans
  simp only [one_div]
  exact ENNReal.inv_le_inv.mpr (pow_le_pow_right₀ (by norm_num) hle)

/-- Exact wire length for every successful signature on every execution path from a
generated secret key. Fixed padding, if used, is included in the bytes. -/
def HasSignatureSize (S : SigScheme) (size : Nat) : Prop :=
  ∀ keys ∈ support S.keygen, ∀ message,
    ∀ signature, some signature ∈ support (S.sign keys.2 message) → signature.length = size

def HasPublicKeySize (S : SigScheme) (size : Nat) : Prop :=
  ∀ keys ∈ support S.keygen, keys.1.length ≤ size

/-- Verification cost includes malformed keys and signatures. -/
def HasVerificationBound (S : SigScheme) (budget : Nat) : Prop :=
  ∀ pk message signature, HasVerifyCost (S.verify pk message signature) budget

end LeanSphincs.Benchmark
