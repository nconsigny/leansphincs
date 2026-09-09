"""Exact arithmetic regressions, never cryptographic eligibility tests."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ots_experiments import experiments, hash_cost, multiply, pareto, power, rank_key, shared_rows


class OTSExperimentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper = experiments("paper", selection="verification")
        cls.rom = experiments("rom32")
        cls.rom_verify = experiments("rom32", selection="verification")

    def test_paper_verification_and_keygen_totals(self):
        self.assertEqual([r["verification"] for r in self.paper], [73, 68, 63, 60])
        self.assertEqual([r["keygen"] for r in self.paper], [168, 168, 159, 167])
        for row in self.paper:
            self.assertGreaterEqual(int(row["eligible_count"]), 2**112)
            self.assertLessEqual(row["padded_signature_bytes"], 2080)

    def test_rom_remetered_product_choices(self):
        self.assertEqual([r["keygen"] for r in self.rom], [198, 241, 283, 424])
        self.assertEqual([r["verification"] for r in self.rom], [105, 128, 140, 166])
        self.assertEqual([r["padded_signature_bytes"] for r in self.rom], [1888, 1648, 1712, 1856])
        for row, verification_only in zip(self.rom, self.rom_verify):
            self.assertGreaterEqual(int(row["eligible_count"]), 2**112)
            self.assertLessEqual(row["padded_signature_bytes"] * row["verification"],
                verification_only["padded_signature_bytes"] * verification_only["verification"])

    def test_meter_includes_address_and_encoding(self):
        self.assertEqual(hash_cost(1, "rom32"), 1)
        self.assertEqual(hash_cost(2, "rom32"), 2)
        self.assertEqual(hash_cost(4, "rom32"), 3)
        self.assertEqual(hash_cost(4, "paper"), 1)
        # Four outputs require two 32-byte queries, not a free 64-byte output.
        self.assertEqual(shared_rows(4, "rom32")[(20, 4)], 1)

    def test_quarter_weight_and_rational_signing(self):
        self.assertEqual(rank_key(2, 16, 3, 5, Fraction(1, 4)), 12960000)
        self.assertEqual(rank_key(2, 16, 3, 5, Fraction(1, 4)),
                         rank_key(4, 1, 3, 5, Fraction(1, 4)))
        self.assertEqual(rank_key(1, 1, Fraction(1, 2), 1, Fraction(1, 4)), Fraction(1, 16))

    def test_invalid_metrics_and_weights(self):
        for beta in [0, -1, 1, 2]:
            with self.assertRaises(ValueError):
                rank_key(1, 1, 1, 1, beta)
        for position in range(4):
            values = [1] * 4
            values[position] = 0
            with self.assertRaises(ValueError):
                rank_key(*values, Fraction(1, 4))

    def test_polynomial_against_exhaustive_toy_enumeration(self):
        choices = [(0, 1), (1, 2), (1, 2), (3, 1)]
        expected = {}
        for sequence in product(choices, repeat=3):
            key = tuple(map(sum, zip(*sequence)))
            if key[0] <= 5 and key[1] <= 5:
                expected[key] = expected.get(key, 0) + 1
        self.assertEqual(power({(0, 1): 1, (1, 2): 2, (3, 1): 1}, 3, 5, 5), expected)
        self.assertEqual(multiply({(0, 0): 1}, expected, 5, 5), expected)

    def test_infeasible_size_is_not_a_candidate(self):
        for row in experiments("rom32", max_values=1):
            self.assertFalse(row["codebook_found"])
            self.assertNotIn("verification", row)

    def test_frontier_keeps_tradeoffs_and_removes_duplicates(self):
        points = [dict(padded_signature_bytes=s, verification=v)
                  for s, v in [(1, 5), (2, 3), (2, 4), (3, 4), (2, 3), (4, 1)]]
        self.assertEqual([(r["padded_signature_bytes"], r["verification"]) for r in pareto(points)],
                         [(1, 5), (2, 3), (4, 1)])

    def test_cli_defaults_to_approved_weight_without_claiming_eligibility(self):
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/ots_experiments.py"),
                   "--profile", "paper", "--signing-work", "1", "--signing-kind", "expected-upper-bound"]
        report = json.loads(subprocess.check_output(command, text=True, timeout=30))
        self.assertEqual(report["beta"], "1/4")
        self.assertFalse(report["experimental_weight_override"])
        self.assertFalse(report["ranked"])
        self.assertFalse(report["security_proved"])
        self.assertFalse(report["costs_certified"])
        invalid = subprocess.run(command + ["--beta", "1"], capture_output=True, text=True, timeout=10)
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main()
