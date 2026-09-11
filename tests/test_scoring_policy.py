from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scoring_policy import additive_score, load_scoring_profile, score_entry
from verify_submission import harness_manifest


class ScoringPolicyTests(unittest.TestCase):
    def test_profile_is_integrity_bound(self):
        self.assertIn("benchmark/scoring.json", harness_manifest()["files"])

    def test_exact_addition_not_product(self):
        self.assertEqual(additive_score(2, 3, Fraction(1, 4)), Fraction(7, 2))
        self.assertEqual(additive_score(2**80, 7, Fraction(1, 3)), Fraction(2**80 + 21, 3))

    def test_unset_organizer_coefficient_cannot_score(self):
        profile = load_scoring_profile(ROOT / "benchmark/scoring.json")
        self.assertIsNone(profile["bandwidth_price"])
        self.assertIsNone(score_entry(profile, 100, 200))

    def test_profile_validation(self):
        base = load_scoring_profile(ROOT / "benchmark/scoring.json")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scoring.json"
            for price in [0.5, {}, {"numerator": True, "denominator": 1},
                          {"numerator": 1, "denominator": 0}, {"numerator": 2, "denominator": 2}]:
                path.write_text(json.dumps(base | {"bandwidth_price": price}))
                with self.assertRaises(ValueError):
                    load_scoring_profile(path)
            path.write_text(json.dumps(base | {"bandwidth_price": {"numerator": 1, "denominator": 8}}))
            profile = load_scoring_profile(path)
            self.assertEqual(score_entry(profile, 16, 4)["value"], "6")

    def test_nonpositive_price_or_metrics_rejected(self):
        for args in [(0, 1, 1), (1, 0, 1), (1, 1, 0), (1, 1, -1)]:
            with self.assertRaises(ValueError):
                additive_score(*args)
