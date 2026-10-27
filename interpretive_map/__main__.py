"""Run the full offline worked example: python3 -m interpretive_map."""
from __future__ import annotations
import argparse
import csv
import html
import io
import json
from pathlib import Path
import platform

from .contracts import digest, load_bundle
from .diagnostics import diagnostics
from .judgments import reference_states
from .profiles import aggregate, apply_corrections, select_cases
from .prompts import build_prompt
from .voting import consensus_rows, parse_cached

ROOT = Path(__file__).resolve().parents[1]


def csv_text(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    return stream.getvalue()


def build_outputs(root=ROOT):
    b = load_bundle(root)
    segments = {s["segment_id"]: s for s in b["segments"]}
    parsed = [parse_cached(j, segments[j["segment_id"]], b["codebook"]) for j in b["model_judgments"]]
    refs = reference_states(b)
    consensus = consensus_rows(b, parsed)
    profiles = aggregate(consensus)
    corrected_rows = apply_corrections(consensus, b["corrections"])
    corrected = aggregate(corrected_rows)
    cases = select_cases(b, profiles, consensus)
    corrected_cases = select_cases(b, corrected, corrected_rows)
    diag = diagnostics(b, refs, consensus, parsed)
    sensitivity = []
    models = [m["model_id"] for m in b["models"]]
    for omitted in models:
        for p in aggregate(consensus_rows(b, parsed, [m for m in models if m != omitted])):
            sensitivity.append({"omitted_model": omitted, **p})
    lineage = []
    for r in consensus:
        s = segments[r["segment_id"]]
        lineage.append({**r, **{k: s[k] for k in ("source_id", "source_paragraphs", "start", "end", "text_sha256", "text")}})
    outputs = {}
    def json_out(name, data):
        outputs[name] = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    json_out("reference_states.json", refs)
    json_out("parsed_model_judgments.json", parsed)
    json_out("segment_lineage.json", lineage)
    json_out("diagnostics.json", diag)
    json_out("case_candidates.json", cases)
    json_out("case_candidates_after_reading.json", corrected_cases)
    json_out("consensus_after_reading.json", corrected_rows)
    json_out("prompts.json", [{"segment_id": s["segment_id"], "code": code, "prompt": build_prompt(s, b["codebook"], code)}
                              for s in b["segments"] if s["gate"] == "eligible" for code in b["codebook"]["codes"]])
    outputs["campaign_profiles.csv"] = csv_text(profiles)
    outputs["campaign_profiles_after_reading.csv"] = csv_text(corrected)
    outputs["model_subset_sensitivity.csv"] = csv_text(sensitivity)
    outputs["errors.csv"] = csv_text(diag["errors"])
    report = ["# Synthetic methods demonstration", "", "**All texts, human judgments, collective deliberations, and model outputs are invented. These numbers are teaching results, not empirical findings or estimates of provider performance.**", "",
              "## Collective code development", "", b["revision"]["problem"], "", *["- " + t for t in b["revision"]["discussion"]], "", b["revision"]["decision"], "",
              "The v0.1 disagreement survives in the raw record. The defended v0.2 calibration labels are distinct records. Holdout and mapping campaigns do not enter the revision event.", "",
              "## Evaluation mechanics", "", "Only explicit collective or adjudicated decisions are evaluation references. Single-coder, unanimous-independent, unresolved, excluded, and gate-uncertain states remain visible in reference_states.json. A model majority is never a human reference.", "",
              "Scores below are conditional on a defended reference and a resolved model prediction. Coverage and counts must travel with every score. Unresolved model outputs are unscored, not negative. No inferential claim is appropriate for this tiny invented example.", "",
              "| Code | Vote rule | Scored / defended | TP / FP / FN / TN | Unscored |", "|---|---|---:|---:|---:|"]
    for d in diag["metrics"]:
        if d["split"] == "holdout" and d["predictor"] in {"majority_fixed", "unanimity_abstain", "any_positive", "all_positive_indicator"}:
            report.append(f"| {d['code']} | {d['predictor']} | {d['n_scored']} / {d['n_defended']} | {d['tp']} / {d['fp']} / {d['fn']} / {d['tn']} | {d['unscored']} |")
    report += ["", "Both model agreement and apparent quote support can coexist with an interpretive error. The frozen holdout contains a unanimous false positive on a rejected allegation. Inspect errors.csv and the original text; do not select the best-looking rule from this holdout.", "",
               "## Provisional map and reading priorities", "", "Each campaign/code/rule reports resolved share, coverage, all-eligible lower and upper bounds, excluded and gate-uncertain counts, and links through segment IDs to source text. Bounds assign unresolved eligible judgments 0 or 1; they are sensitivity ranges, not confidence intervals or validity guarantees. Word and segment weighting are both exported.", ""]
    for c in cases:
        report += [f"- {c['campaign_id']}: {', '.join(c['reasons'])}. {c['independence_note']}."]
    report += ["", "Model-subset sensitivity drops each simulated model in turn. With two remaining models, a split vote abstains under strict majority. This comparison is a stress test, not a search for the most favorable electorate.", "",
               "## Worked return to text", "", "The original majority map provisionally nominates SYN-M01 as a concealment example. All three simulated models mark its first passage positive:", "", "> " + segments["SYN-M01:0"]["text"], "", "Reading the next passage changes the case interpretation:", "", "> " + b["corrections"][0]["context_quote"], "", b["corrections"][0]["rationale"], ""]
    for before, after in zip(profiles, corrected):
        if before["campaign_id"] == "SYN-M01" and before["code"] == "concealed_reversal" and before["rule"] == "majority_fixed" and before["weighting"] == "segment":
            report += [f"The provisional majority share changes from {before['positive_n']}/{before['resolved_n']} ({before['share_resolved']:.0%}) to {after['positive_n']}/{after['resolved_n']} ({after['share_resolved']:.0%}). The incomplete third passage stays gate-uncertain and outside this eligible denominator.", ""]
    report += [b["corrections"][0]["case_decision"], "", "The correction is an explicit analytical overlay (RETURN-001). Raw judgments, original map, and held-out scores remain frozen. The corrected candidate output records the changed reading role. A context-window change would require a new prompt/cache version and fresh evaluation material.", "",
               "SYN-M02 and SYN-M03 share a fictional target and overlapping windows. Their candidate records request joint reading. This is a sampling caution, not a financial result or a causal identification claim.", "",
               "## Limits", "", "The gate is prepared by the synthetic fixture, not inferred. This demo implements two teaching codes, deterministic aggregation and reading priorities; it does not implement the nine-code empirical scheme, segmentation models, a coding UI, inference clients, clustering, or financial analysis. See docs/AUDIT_CHECKLIST.md before any empirical use."]
    outputs["report.md"] = "\n".join(report) + "\n"
    # Static local review page: no CDN, tracking, scripts, or external requests.
    card_rows = []
    for s in b["segments"]:
        rows = [r for r in consensus if r["segment_id"] == s["segment_id"] and r["rule"] == "majority_fixed"]
        readings = " · ".join(f"{r['code']}: {r['value'] if r['value'] is not None else 'unresolved'}" for r in rows)
        card_rows.append(f'<details id="{html.escape(s["segment_id"])}"><summary>{html.escape(s["segment_id"])} — {html.escape(readings)}</summary><p>{html.escape(s["text"])}</p><p class="meta">{html.escape(s["source_id"])} · characters [{s["start"]}, {s["end"]}) · gate: {html.escape(s["gate"])} · SHA-256 {s["text_sha256"]}</p></details>')
    outputs["review.html"] = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Synthetic interpretation review</title><style>body{max-width:980px;margin:3rem auto;padding:0 1.5rem;background:#f7f5f0;color:#173638;font:18px/1.65 system-ui}h1{font-size:2.5rem}details{background:white;padding:1rem;margin:1rem 0;border:1px solid #bccac4;border-radius:8px}summary{cursor:pointer;font-weight:600}.meta{font:13px/1.6 monospace;overflow-wrap:anywhere}pre{white-space:pre-wrap;font:16px/1.7 system-ui}.notice{border-left:5px solid #af562f;padding:1rem;background:#fff0e5}</style><h1>From interpretations to provisional maps</h1><p class="notice">Synthetic teaching artifact. All passages and judgments are invented. No empirical results or real model performance are reported.</p><h2>Worked demonstration</h2><pre>' + html.escape(outputs["report.md"]) + '</pre><h2>Return to every segment</h2>' + "\n".join(card_rows) + '</html>\n'
    run_manifest = {"synthetic": True, "artifact_version": "0.1.0", "fixture_version": b["manifest"]["fixture_version"],
                    "inputs_sha256": b["manifest"]["sha256"],
                    "code_sha256": {str(p.relative_to(root)): digest(p.read_bytes()) for p in sorted((root / "interpretive_map").glob("*.py"))},
                    "output_sha256": {name: digest(content) for name, content in sorted(outputs.items())},
                    "reproducibility": "No clock, random, network, DB, or environment-sensitive paths in analytic outputs; runtime recorded separately.",
                    "counts": {"campaigns": len(b["campaigns"]), "segments": len(b["segments"]), "raw_human_judgments": len(b["human_judgments"]),
                               "collective_decisions": len(b["decisions"]), "cached_model_responses": len(parsed), "campaign_profile_rows": len(profiles),
                               "model_subset_profile_rows": len(sensitivity), "case_candidates": len(cases)}}
    json_out("run_manifest.json", run_manifest)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/demo", help="New output directory within this repository; must not already exist")
    args = parser.parse_args()
    destination = (ROOT / args.output).resolve()
    output_root = (ROOT / "outputs").resolve()
    if not output_root.is_relative_to(ROOT.resolve()) or not destination.is_relative_to(output_root):
        parser.error("Output must be under this repository's outputs/ directory")
    if destination.exists():
        parser.error("Output directory already exists; choose a new --output outputs/NAME to preserve the earlier run")
    outputs = build_outputs()
    destination.mkdir(parents=True)
    for name, content in outputs.items():
        (destination / name).write_text(content, encoding="utf-8")
    (destination / "environment.json").write_text(json.dumps({"python": platform.python_version(), "implementation": platform.python_implementation(), "external_dependencies": []}, indent=2) + "\n")
    counts = json.loads(outputs["run_manifest.json"])["counts"]
    print("SYNTHETIC OFFLINE DEMO COMPLETE")
    print(json.dumps(counts, indent=2))
    print(f"Read {destination.relative_to(ROOT)}/report.md or review.html")


if __name__ == "__main__":
    main()
