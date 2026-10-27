"""Individual responses remain separate from explicit collective resolutions."""
from collections import defaultdict


def reference_states(bundle):
    version = bundle["codebook"]["version"]
    individual = defaultdict(list)
    for j in bundle["human_judgments"]:
        if j["codebook_version"] == version:
            individual[(j["segment_id"], j["code"])].append(j)
    decisions = {(d["segment_id"], d["code"]): d for d in bundle["decisions"]}
    result = []
    for s in bundle["segments"]:
        for code in bundle["codebook"]["codes"]:
            key = s["segment_id"], code
            js = individual[key]
            d = decisions.get(key)
            value = None
            if s["gate"] != "eligible":
                state = "excluded" if s["gate"] == "excluded" else "gate_uncertain"
            elif d:
                state, value = d["kind"], d["value"]
            elif len({j["pool"] for j in js}) > 1:
                state = "multiple_pools_require_resolution"
            elif not js:
                state = "no_reference"
            elif len(js) == 1:
                state = "single_coder"
            elif any(j["value"] is None for j in js):
                state = "unresolved"
            elif len({j["value"] for j in js}) == 1:
                state = "unanimous_individual"
            else:
                state = "unresolved"
            result.append({"segment_id": key[0], "campaign_id": s["campaign_id"], "code": code,
                           "state": state, "value": value, "judgment_ids": [j["judgment_id"] for j in js],
                           "decision_id": d["decision_id"] if d else None})
    return result
