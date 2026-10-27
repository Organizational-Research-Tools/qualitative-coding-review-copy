"""Provisional corpus maps retain uncertainty, denominators, and text lineage."""
from collections import defaultdict
from .diagnostics import ratio


def aggregate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["campaign_id"], r["code"], r["rule"])].append(r)
    result = []
    for (campaign, code, rule), group in sorted(groups.items()):
        eligible = [r for r in group if r["gate"] == "eligible"]
        resolved = [r for r in eligible if r["value"] is not None]
        yes = [r for r in resolved if r["value"] == 1]
        unknown = [r for r in eligible if r["value"] is None]
        for weighting in ("segment", "word"):
            weight = lambda r: 1 if weighting == "segment" else r["word_weight"]
            total, known, positive, uncertain = (sum(weight(r) for r in rs) for rs in (eligible, resolved, yes, unknown))
            result.append({"campaign_id": campaign, "code": code, "rule": rule, "weighting": weighting,
                           "eligible_n": len(eligible), "resolved_n": len(resolved), "positive_n": len(yes),
                           "unknown_n": len(unknown), "excluded_n": sum(r["gate"] == "excluded" for r in group),
                           "gate_uncertain_n": sum(r["gate"] == "uncertain" for r in group),
                           "eligible_weight": total, "resolved_weight": known, "positive_weight": positive,
                           "coverage": ratio(known, total), "share_resolved": ratio(positive, known),
                           "lower_bound_eligible": ratio(positive, total), "upper_bound_eligible": ratio(positive + uncertain, total),
                           "segment_ids": [r["segment_id"] for r in group],
                           "positive_segment_ids": [r["segment_id"] for r in yes],
                           "unknown_segment_ids": [r["segment_id"] for r in unknown],
                           "correction_ids": [r["correction_id"] for r in group if r["correction_id"]]})
    return result


def apply_corrections(rows, corrections):
    lookup = {(c["segment_id"], c["code"]): c for c in corrections}
    result = []
    for row in rows:
        c = lookup.get((row["segment_id"], row["code"]))
        result.append({**row, "value": c["value"], "correction_id": c["correction_id"]} if c else dict(row))
    return result


def select_cases(bundle, profiles, rows):
    """Transparent reading priorities, not estimated latent clusters."""
    candidates = []
    for c in bundle["campaigns"]:
        if c["split"] != "mapping":
            continue
        ps = [p for p in profiles if p["campaign_id"] == c["campaign_id"] and p["weighting"] == "segment"]
        changes = 0
        for code in bundle["codebook"]["codes"]:
            values = {p["lower_bound_eligible"] for p in ps if p["code"] == code}
            changes += int(len(values) > 1)
        unknowns = max((p["unknown_n"] for p in ps), default=0)
        gate_uncertain = max((p["gate_uncertain_n"] for p in ps), default=0)
        baseline = [p for p in ps if p["rule"] == "majority_fixed"]
        positive_codes = sum(p["positive_n"] > 0 for p in baseline)
        reasons = []
        if changes:
            reasons.append("vote_rule_sensitive")
        if unknowns or gate_uncertain:
            reasons.append("uncertainty_to_investigate")
        if positive_codes:
            reasons.append("provisional_positive_example_requires_reading")
        else:
            reasons.append("negative_comparison")
        overlaps = [other["campaign_id"] for other in bundle["campaigns"]
                    if other["campaign_id"] != c["campaign_id"] and other["target_id"] == c["target_id"]
                    and max(c["window"][0], other["window"][0]) <= min(c["window"][1], other["window"][1])]
        candidates.append({"campaign_id": c["campaign_id"], "reasons": reasons,
                           "sensitive_code_count": changes, "max_unknown_segments": unknowns,
                           "gate_uncertain_segments": gate_uncertain,
                           "provisional_positive_codes": positive_codes, "overlapping_campaigns": overlaps,
                           "independence_note": "Read jointly; overlapping synthetic windows" if overlaps else "No overlap among supplied synthetic windows; not a general confound screen",
                           "segment_ids": sorted({r["segment_id"] for r in rows if r["campaign_id"] == c["campaign_id"]})})
    return sorted(candidates, key=lambda c: (-c["sensitive_code_count"], -c["max_unknown_segments"], c["campaign_id"]))
