"""Conditional validity diagnostics against an explicit, frozen human reference."""
from collections import Counter


def ratio(a, b):
    return a / b if b else None


def diagnostics(bundle, references, consensus, parsed):
    campaigns = {c["campaign_id"]: c for c in bundle["campaigns"]}
    results, errors = [], []
    predictors = {}
    for row in consensus:
        predictors.setdefault(row["rule"], {})[(row["segment_id"], row["code"])] = row["value"]
    for model in bundle["models"]:
        predictors[model["model_id"]] = {(j["segment_id"], j["code"]): j["value"] for j in parsed
                                          if j["model_id"] == model["model_id"]}
    for split in ("calibration", "holdout"):
        for code in bundle["codebook"]["codes"]:
            refs = [r for r in references if campaigns[r["campaign_id"]]["split"] == split and r["code"] == code]
            defended = [r for r in refs if r["state"] in {"collective", "adjudicated"}]
            for predictor, values in predictors.items():
                counts = Counter()
                for r in defended:
                    pred = values.get((r["segment_id"], code))
                    truth = r["value"]
                    outcome = "unscored" if pred is None else { (1, 1): "tp", (0, 1): "fp", (1, 0): "fn", (0, 0): "tn" }[(truth, pred)]
                    counts[outcome] += 1
                    if outcome in {"fp", "fn", "unscored"}:
                        errors.append({"split": split, "code": code, "predictor": predictor,
                                       "segment_id": r["segment_id"], "outcome": outcome,
                                       "reference": truth, "prediction": pred, "decision_id": r["decision_id"]})
                tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
                scored = tp + fp + fn + tn
                results.append({"split": split, "code": code, "predictor": predictor,
                                "reference_states": dict(Counter(r["state"] for r in refs)),
                                "n_defended": len(defended), "n_scored": scored,
                                "tp": tp, "fp": fp, "fn": fn, "tn": tn, "unscored": counts["unscored"],
                                "coverage": ratio(scored, len(defended)),
                                "reference_positive_share": ratio(sum(r["value"] for r in defended), len(defended)),
                                "accuracy_on_scored": ratio(tp + tn, scored),
                                "precision_on_scored": ratio(tp, tp + fp),
                                "recall_on_scored": ratio(tp, tp + fn),
                                "f1_on_scored": ratio(2 * tp, 2 * tp + fp + fn),
                                "detected_fraction_of_all_defended_positives": ratio(tp, sum(r["value"] for r in defended))})
    return {"synthetic": True, "interpretation": "Descriptive mechanics only; neither model performance estimates nor proof of construct validity.",
            "metrics": results, "errors": errors,
            "cache_status_counts": dict(Counter(j["status"] for j in parsed))}
