"""Missing, malformed, and abstaining model judgments never become zero votes."""
import json
from .contracts import require
from .prompts import prompt_hash

RULES = ("majority_fixed", "unanimity_abstain", "any_positive", "all_positive_indicator")


def parse_cached(row, segment, codebook):
    require(row["prompt_sha256"] == prompt_hash(segment, codebook, row["code"]), "Cache/prompt mismatch")
    status, value, evidence, rationale = "invalid", None, "", ""
    error = None
    try:
        payload = json.loads(row["raw_response"])
        require(isinstance(payload, dict) and set(payload) == {"value", "evidence", "rationale"}, "Response fields")
        require(isinstance(payload["rationale"], str) and bool(payload["rationale"].strip()), "Missing rationale")
        require(isinstance(payload["evidence"], str), "Evidence must be text")
        v = payload["value"]
        require(v is None or type(v) is int and v in (0, 1), "Non-binary response")
        evidence, rationale = payload["evidence"], payload["rationale"]
        if v is None:
            status = "abstain"
        else:
            require(bool(evidence) and evidence in segment["text"], "Evidence quote not in passage")
            status, value = "valid", v
    except (ValueError, TypeError) as exc:
        error = str(exc)
    return {**{k: row[k] for k in ("judgment_id", "segment_id", "code", "model_id")},
            "status": status, "value": value, "evidence": evidence, "rationale": rationale, "error": error}


def vote(values, expected, rule):
    require(rule in RULES, f"Unknown rule: {rule}")
    require(expected > 0 and len(values) <= expected, "Invalid electorate")
    require(all(type(v) is int and v in (0, 1) for v in values), "Invalid vote")
    yes, no = values.count(1), values.count(0)
    if rule == "majority_fixed":
        return 1 if yes > expected / 2 else 0 if no > expected / 2 else None
    if rule == "unanimity_abstain":
        return values[0] if len(values) == expected and len(set(values)) == 1 else None
    if rule == "any_positive":
        return 1 if yes else 0 if no == expected else None
    return int(yes == expected) if len(values) == expected else None


def consensus_rows(bundle, parsed, models=None):
    models = models if models is not None else [m["model_id"] for m in bundle["models"]]
    require(len(models) > 0 and len(set(models)) == len(models), "Invalid model selection")
    require(set(models) <= {m["model_id"] for m in bundle["models"]}, "Unknown selected model")
    indexed = {(j["segment_id"], j["code"], j["model_id"]): j for j in parsed}
    rows = []
    for s in bundle["segments"]:
        for code in bundle["codebook"]["codes"]:
            js = [indexed.get((s["segment_id"], code, m)) for m in models]
            valid = [j["value"] for j in js if j and j["status"] == "valid"]
            counts = {state: sum(1 for j in js if (j["status"] if j else "missing") == state)
                      for state in ("valid", "missing", "invalid", "abstain")}
            for rule in RULES:
                value = vote(valid, len(models), rule) if s["gate"] == "eligible" else None
                rows.append({"segment_id": s["segment_id"], "campaign_id": s["campaign_id"],
                             "code": code, "rule": rule, "value": value, "gate": s["gate"],
                             "models": models, "expected": len(models), "counts": counts,
                             "disagreement": len(set(valid)) > 1,
                             "judgment_ids": [j["judgment_id"] for j in js if j],
                             "word_weight": len(s["text"].split()), "correction_id": None})
    return rows
