"""Boundary tests protect the scientific distinctions, not just happy paths."""
import copy
import json
from pathlib import Path
import socket
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from interpretive_map.__main__ import ROOT, build_outputs
from interpretive_map.contracts import load_bundle, validate_bundle
from interpretive_map.diagnostics import diagnostics
from interpretive_map.judgments import reference_states
from interpretive_map.profiles import aggregate, apply_corrections, select_cases
from interpretive_map.voting import consensus_rows, parse_cached, vote


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.b = load_bundle(ROOT)
        segments = {s["segment_id"]: s for s in self.b["segments"]}
        self.parsed = [parse_cached(j, segments[j["segment_id"]], self.b["codebook"]) for j in self.b["model_judgments"]]
        self.rows = consensus_rows(self.b, self.parsed)

    def test_reference_states_are_not_conflated(self):
        states = {(r["segment_id"], r["code"]): r for r in reference_states(self.b)}
        for key, state in [(('SYN-H02:0', 'concealed_reversal'), 'unresolved'), (('SYN-H02:0', 'structural_trap'), 'single_coder'),
                           (('SYN-H02:1', 'concealed_reversal'), 'unanimous_individual'), (('SYN-H02:2', 'concealed_reversal'), 'excluded'),
                           (('SYN-M01:2', 'concealed_reversal'), 'gate_uncertain')]:
            self.assertEqual(states[key]["state"], state)
            self.assertIsNone(states[key]["value"])
        self.assertEqual(states[('SYN-H01:2', 'concealed_reversal')]["state"], 'adjudicated')

    def test_duplicate_pools_cannot_overwrite(self):
        j = copy.deepcopy(next(j for j in self.b["human_judgments"] if j["segment_id"] == "SYN-H02:1"))
        j.update(pool="second_pool", judgment_id="extra", value=1)
        self.b["human_judgments"].append(j)
        validate_bundle(self.b)
        r = next(r for r in reference_states(self.b) if r["segment_id"] == j["segment_id"] and r["code"] == j["code"])
        self.assertEqual(r["state"], "multiple_pools_require_resolution")
        self.assertIsNone(r["value"])

    def test_duplicate_cache_rejected(self):
        self.b["model_judgments"].append(copy.deepcopy(self.b["model_judgments"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_bundle(self.b)

    def test_holdout_leakage_rejected(self):
        self.b["revision"]["development_segments"].append("SYN-H01:0")
        with self.assertRaisesRegex(ValueError, "Holdout/mapping"):
            validate_bundle(self.b)

    def test_text_span_corruption_rejected(self):
        self.b["segments"][0]["start"] += 1
        with self.assertRaisesRegex(ValueError, "span mismatch"):
            validate_bundle(self.b)

    def test_version_and_reference_mismatch_rejected(self):
        self.b["decisions"][0]["judgment_ids"][0] = self.b["decisions"][1]["judgment_ids"][0]
        with self.assertRaisesRegex(ValueError, "references mismatch"):
            validate_bundle(self.b)

    def test_missing_malformed_abstaining_are_distinct(self):
        invalid = [j for j in self.parsed if j["status"] == "invalid"]
        self.assertEqual(len(invalid), 1)
        self.assertIsNone(invalid[0]["value"])
        r = next(r for r in self.rows if r["segment_id"] == "SYN-H02:1" and r["code"] == "concealed_reversal" and r["rule"] == "majority_fixed")
        self.assertEqual(r["counts"], {"valid": 1, "missing": 1, "abstain": 1, "invalid": 0})
        self.assertIsNone(r["value"])

    def test_invalid_quote_and_boolean_labels_do_not_become_valid_votes(self):
        j = copy.deepcopy(self.b["model_judgments"][0])
        s = self.b["segments"][0]
        for value, evidence in [(1, "invented nonexistent evidence"), (True, s["text"]), ("1", s["text"])]:
            j["raw_response"] = json.dumps({"value": value, "evidence": evidence, "rationale": "A test reading"})
            self.assertEqual(parse_cached(j, s, self.b["codebook"])["status"], "invalid")

    def test_cache_bound_to_exact_prompt(self):
        j = copy.deepcopy(self.b["model_judgments"][0])
        j["prompt_sha256"] = "changed"
        with self.assertRaisesRegex(ValueError, "Cache/prompt"):
            parse_cached(j, self.b["segments"][0], self.b["codebook"])

    def test_vote_quorum_and_unanimity_semantics(self):
        self.assertIsNone(vote([1], 3, "majority_fixed"))
        self.assertEqual(vote([1, 1], 3, "majority_fixed"), 1)
        self.assertIsNone(vote([1, 0], 2, "majority_fixed"))
        self.assertIsNone(vote([1, 1], 3, "unanimity_abstain"))
        self.assertIsNone(vote([1, 1, 0], 3, "unanimity_abstain"))
        self.assertEqual(vote([1, 1, 0], 3, "all_positive_indicator"), 0)
        self.assertEqual(vote([1], 3, "any_positive"), 1)
        self.assertIsNone(vote([0, 0], 3, "any_positive"))

    def test_coverage_bounds_and_gates(self):
        profiles = aggregate(self.rows)
        p = next(p for p in profiles if p["campaign_id"] == "SYN-H02" and p["code"] == "concealed_reversal" and p["rule"] == "majority_fixed" and p["weighting"] == "segment")
        self.assertEqual((p["eligible_n"], p["excluded_n"], p["unknown_n"]), (2, 1, 2))
        self.assertEqual((p["lower_bound_eligible"], p["upper_bound_eligible"]), (0, 1))
        self.assertIsNone(p["share_resolved"])
        self.assertEqual(p["coverage"], 0)

    def test_empty_eligible_denominator_is_not_zero_prevalence(self):
        rows = [r for r in self.rows if r["segment_id"] == "SYN-H02:2"]
        for p in aggregate(rows):
            self.assertIsNone(p["lower_bound_eligible"])
            self.assertIsNone(p["coverage"])

    def test_unanimous_error_survives_agreement(self):
        d = diagnostics(self.b, reference_states(self.b), self.rows, self.parsed)
        error = next(e for e in d["errors"] if e["segment_id"] == "SYN-H01:2" and e["predictor"] == "unanimity_abstain" and e["code"] == "concealed_reversal")
        self.assertEqual(error["outcome"], "fp")
        majority = next(m for m in d["metrics"] if m["split"] == "holdout" and m["predictor"] == "majority_fixed" and m["code"] == "concealed_reversal")
        self.assertEqual((majority["n_defended"], majority["tp"], majority["fp"], majority["tn"]), (3, 1, 1, 1))

    def test_correction_is_overlay_and_changes_reading_role(self):
        before = copy.deepcopy(self.rows)
        revised = apply_corrections(self.rows, self.b["corrections"])
        self.assertEqual(self.rows, before)
        cases = select_cases(self.b, aggregate(revised), revised)
        case = next(c for c in cases if c["campaign_id"] == "SYN-M01")
        self.assertEqual(case["provisional_positive_codes"], 0)
        self.assertIn("negative_comparison", case["reasons"])
        self.assertTrue(any(r["correction_id"] == "RETURN-001" for r in revised))

    def test_corrections_cannot_rewrite_holdout(self):
        self.b["corrections"][0]["segment_id"] = "SYN-H01:0"
        with self.assertRaisesRegex(ValueError, "cannot change evaluation"):
            validate_bundle(self.b)

    def test_overlapping_windows_flagged(self):
        cases = select_cases(self.b, aggregate(self.rows), self.rows)
        self.assertEqual(next(c for c in cases if c["campaign_id"] == "SYN-M02")["overlapping_campaigns"], ["SYN-M03"])

    def test_end_to_end_is_deterministic_and_offline(self):
        with patch.object(socket, "socket", side_effect=AssertionError("Network forbidden")), patch.object(sqlite3, "connect", side_effect=AssertionError("Database forbidden")):
            first = build_outputs()
            second = build_outputs()
        self.assertEqual(first, second)
        manifest = json.loads(first["run_manifest.json"])
        self.assertEqual(manifest["counts"]["segments"], 16)
        self.assertEqual(manifest["counts"]["cached_model_responses"], 82)
        self.assertEqual(manifest["counts"]["campaign_profile_rows"], 96)

    def test_changed_frozen_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "fixtures/synthetic").mkdir(parents=True)
            manifest = {"synthetic": True, "sha256": {"input.json": "wrong"}, "inputs": {}}
            (root / "fixtures/synthetic/manifest.json").write_text(json.dumps(manifest))
            (root / "input.json").write_text("[]")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_bundle(root)


if __name__ == "__main__":
    unittest.main()
