#!/usr/bin/env python3
"""Author invented teaching data; never import empirical data or call a model.

This intentionally rewrites the synthetic fixture and its freeze manifest.
Normal demonstration runs only READ these frozen files.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from interpretive_map.contracts import digest
from interpretive_map.prompts import prompt_hash


def write(relative, data):
    (ROOT / relative).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def build():
    codes = {
        "concealed_reversal": {
            "name": "Concealment followed by revelation",
            "definition": "The passage advances a story in which actors conceal a material condition and its later revelation changes others' understanding or action.",
            "include": ["Identify who conceals, what is concealed, and a revelation or discovery in an event sequence.", "An author's allegation can instantiate the story without proving the allegation true."],
            "exclude": ["Disappointment or reversal without concealment and revelation.", "An allegation merely quoted and rejected by the author; read surrounding text to establish stance."],
            "uncertainty": "Preserve uncertainty if the actor, sequence, or author's stance cannot be resolved from the available context."
        },
        "structural_trap": {
            "name": "Self-defeating operating sequence",
            "definition": "The passage advances an event sequence in which the operating arrangement itself produces a worsening consequence even as actors follow it.",
            "include": ["Name the repeated or linked actions, the arrangement connecting them, and the worsening consequence."],
            "exclude": ["A bad outcome alone, a static unfavorable ratio, or a single execution mistake.", "A mechanism the author quotes only to reject."],
            "uncertainty": "Retain rival interpretations of mechanism and temporality."
        }
    }
    book = {"version": "0.2.0", "synthetic": True, "scope": "Two teaching codes inspired by narrative coding; not the project's nine-trope codebook.",
            "unit": "Prepared segment interpreted in its document context", "multi_label": "Both may occur if the text supports distinct mechanisms; defend each assignment.",
            "freeze_event": "F2: after synthetic collective revision, before evaluation", "codes": codes}
    previous = json.loads(json.dumps(book))
    previous["version"] = "0.1.0"
    previous["freeze_event"] = "F1: initial exploratory definition"
    previous["codes"]["concealed_reversal"]["definition"] = "A story in which a favorable public appearance gives way to a damaging reversal."
    previous["codes"]["concealed_reversal"]["include"] = ["Identify an appearance and a later damaging reversal; the role of concealment needs collective clarification."]
    previous["codes"]["concealed_reversal"]["exclude"] = ["Static criticism without an event sequence."]
    write("codebooks/v0.1.0.json", previous)
    write("codebooks/v0.2.0.json", book)
    definitions = [
        ("SYN-C01", "calibration", "SYN-T01", [0, 2], [
            ("A failed launch", "Lumen promised a launch in spring. A supplier strike delayed the launch until winter.", "eligible"),
            ("Hidden tests", "Lumen's managers hid failed tests. An engineer released the logs, and customers cancelled their orders.", "eligible"),
            ("Operating trap", "To meet delivery promises, Lumen added rush orders. Rush orders displaced maintenance, so breakdowns caused further delays.", "eligible")]),
        ("SYN-H01", "holdout", "SYN-T02", [0, 2], [
            ("Revelation", "Cedar's directors hid cancelled contracts. A clerk disclosed the cancellations, and lenders withdrew credit.", "eligible"),
            ("Growth trap", "Cedar opened new depots to serve distant clients. Every new depot increased empty return trips, which drained funds needed for service.", "eligible"),
            ("Rejected allegation", "Critics said Cedar hid losses until an audit exposed them. We reject that account: the audit found the losses were already disclosed.", "eligible")]),
        ("SYN-H02", "holdout", "SYN-T03", [0, 2], [
            ("Ambiguous sequence", "A clerk changed the ledger. Later the public totals changed; the fragment does not tell us whether the earlier totals were concealed or corrected.", "eligible"),
            ("Ordinary sequence", "The board met on Monday. The company opened its scheduled branch on Tuesday.", "eligible"),
            ("Disclosure", "This entirely fictional document is a teaching example.", "excluded")]),
        ("SYN-M01", "mapping", "SYN-T04", [0, 2], [
            ("The allegation", "A rival claimed that Vale concealed failed orders until a technician revealed them and buyers fled.", "eligible"),
            ("Our reading of the record", "We tested the rival's story. The dated notices showed that the orders had been disclosed before the technician spoke; we reject the concealment account.", "eligible"),
            ("Damaged fragment", "Then the records ... [missing fictional page] ... the buyers ...", "uncertain")]),
        ("SYN-M02", "mapping", "SYN-T05", [10, 31], [
            ("Capacity trap", "Moss added clients to cover fixed costs. Each client required a dedicated machine, so expansion raised fixed costs faster than revenue.", "eligible"),
            ("A contested revelation", "Moss removed a failed test from its brochure. A reviewer found the archived brochure, and customers asked for refunds.", "eligible")]),
        ("SYN-M03", "mapping", "SYN-T05", [19, 40], [
            ("Routine change", "Moss replaced a machine on Monday. Production resumed on Tuesday, as planned.", "eligible"),
            ("A disputed mechanism", "Moss added a second shift after demand rose. Repairs increased next month, but this passage does not establish whether shift expansion caused them.", "eligible")])
    ]
    campaigns, sources, segments = [], [], []
    for cid, split, target, window, passages in definitions:
        campaigns.append({"campaign_id": cid, "split": split, "target_id": target, "window": window, "synthetic": True})
        full = "\n\n".join(text for _, text, _ in passages)
        source_id = cid + "-DOC"
        sources.append({"source_id": source_id, "campaign_id": cid, "synthetic": True, "text": full,
                        "origin": "Invented for this artifact; no empirical report or real company is represented.", "sha256": digest(full)})
        start = 0
        for index, (title, text, gate) in enumerate(passages):
            segments.append({"segment_id": f"{cid}:{index}", "campaign_id": cid, "source_id": source_id,
                             "segment_index": index, "source_paragraphs": [index], "start": start, "end": start + len(text),
                             "offset_unit": "Unicode code points, half-open", "text": text, "text_sha256": digest(text),
                             "gate": gate, "gate_reason": {"eligible": "Synthetic prepared narrative passage", "excluded": "Teaching disclosure; not substantive narrative", "uncertain": "Incomplete text prevents confident routing"}[gate],
                             "context": {"position": f"{index + 1}/{len(passages)}", "preceding_titles": [x[0] for x in passages[:index]],
                                         "following_title": passages[index + 1][0] if index + 1 < len(passages) else None}})
            start += len(text) + 2
    lookup = {s["segment_id"]: s for s in segments}
    humans, decisions = [], []
    truth = {"SYN-C01:0": [0, 0], "SYN-C01:1": [1, 0], "SYN-C01:2": [0, 1],
             "SYN-H01:0": [1, 0], "SYN-H01:1": [0, 1], "SYN-H01:2": [0, 0]}
    for sid, values in truth.items():
        for code, value in zip(codes, values):
            refs = []
            for coder in ("reader_a", "reader_b"):
                jid = f"H-{sid}-{code}-{coder}-v2"
                refs.append(jid)
                raw_value = 1 if sid == "SYN-H01:2" and code == "concealed_reversal" and coder == "reader_a" else value
                humans.append({"judgment_id": jid, "segment_id": sid, "code": code, "coder": coder,
                               "pool": "synthetic_" + ("development" if "C01" in sid else "evaluation"), "codebook_version": "0.2.0", "value": raw_value,
                               "rationale": "Invented individual reading: " + ("a concealment/revelation or worsening mechanism appears" if raw_value else "the required pattern is absent or rejected")})
            decisions.append({"decision_id": f"D-{sid}-{code}", "segment_id": sid, "code": code, "codebook_version": "0.2.0",
                              "kind": "adjudicated" if sid == "SYN-H01:2" and code == "concealed_reversal" else "collective", "value": value,
                              "participants": ["reader_a", "reader_b"], "judgment_ids": refs,
                              "rationale": "Synthetic collective reading: apply the sequence and author-stance criteria; a rejected allegation is not an endorsed story. No claim that the described events are true."})
    for coder, value in (("reader_a", 1), ("reader_b", 0)):
        humans.append({"judgment_id": f"H-SYN-C01:0-concealed_reversal-{coder}-v1", "segment_id": "SYN-C01:0", "code": "concealed_reversal",
                       "coder": coder, "pool": "synthetic_development", "codebook_version": "0.1.0", "value": value,
                       "rationale": "Appearance-to-reversal fits the initial wording." if value else "Delay alone does not imply concealment."})
    for code, pairs in {"concealed_reversal": [("reader_a", 1), ("reader_b", None)], "structural_trap": [("reader_a", 0)]}.items():
        for coder, value in pairs:
            humans.append({"judgment_id": f"H-SYN-H02:0-{code}-{coder}", "segment_id": "SYN-H02:0", "code": code, "coder": coder,
                           "pool": "synthetic_evaluation", "codebook_version": "0.2.0", "value": value, "rationale": "Fragment permits competing readings; discussion is not yet resolved."})
    for code in codes:
        for coder in ("reader_a", "reader_b"):
            humans.append({"judgment_id": f"H-SYN-H02:1-{code}-{coder}", "segment_id": "SYN-H02:1", "code": code, "coder": coder,
                           "pool": "synthetic_evaluation", "codebook_version": "0.2.0", "value": 0, "rationale": "Routine sequence lacks this mechanism; independent reading, no collective review recorded."})
    revision = {"synthetic": True, "from_version": "0.1.0", "to_version": "0.2.0", "development_segments": ["SYN-C01:0", "SYN-C01:1", "SYN-C01:2"],
                "participants": ["reader_a", "reader_b"], "problem": "Readers disagreed about whether a failed promise suffices; the broad appearance/reversal wording concealed different mechanisms.",
                "discussion": ["Reader A defended the appearance-to-reversal reading of the launch delay.", "Reader B compared the delay with hidden test results and asked where concealment and discovery occurred.", "The pair retained the more demanding concealment-revelation relation and added explicit author-stance and uncertainty guidance; they did not merge all negative events to improve agreement."],
                "decision": "Clarify the interpretive claim, record the counterexample, and preserve the original disagreement. The launch delay becomes a defended negative in v0.2.",
                "sequence": ["F1 individual v0.1 readings", "F2 collective revision and codebook freeze", "F3 new v0.2 readings and collective decisions", "F4 frozen simulated judgments and evaluation", "F5 mapping-case close reading"],
                "holdout_policy": "No holdout text or evaluation outcome was used to develop the codebook in this designed teaching chronology. All records are invented, so this is not evidence of actual prospective blinding."}
    models = [{"model_id": f"simulated_{name}", "simulated": True, "provider": None, "model_version": "teaching-cache-1", "run_id": f"SYN-RUN-{name}", "generation": "Authored responses, no inference or paid calls"} for name in "abc"]
    # Each triple is an invented electorate, not an actual provider output.
    votes = {
        "SYN-C01:0": [[0, 0, 0], [0, 0, 0]], "SYN-C01:1": [[1, 1, 1], [0, 0, 0]], "SYN-C01:2": [[0, 0, 0], [1, 1, 1]],
        "SYN-H01:0": [[1, 1, 0], [0, 0, 0]], "SYN-H01:1": [[0, 0, 0], [1, 0, 0]], "SYN-H01:2": [[1, 1, 1], [0, 0, 0]],
        "SYN-H02:0": [[1, None, 0], [0, 0, 0]], "SYN-H02:1": [[None, 1, "missing"], [0, 0, 0]],
        "SYN-M01:0": [[1, 1, 1], [0, 0, 0]], "SYN-M01:1": [[0, 0, 0], [0, 0, 0]],
        "SYN-M02:0": [[0, 0, 0], [0, 1, 1]], "SYN-M02:1": [[1, 1, 0], [0, 0, "invalid"]],
        "SYN-M03:0": [["missing", 0, 0], [0, 0, 0]], "SYN-M03:1": [[0, 0, 0], [0, 0, 1]]}
    cache = []
    for sid, per_code in votes.items():
        for code, triple in zip(codes, per_code):
            for model, value in zip(models, triple):
                if value == "missing":
                    continue
                payload = {"value": value, "evidence": lookup[sid]["text"],
                           "rationale": "Simulated response: " + ("the passage appears to contain the mechanism" if value == 1 else "no endorsed instance identified" if value == 0 else "uncertain interpretation")}
                raw = '{"value":' if value == "invalid" else json.dumps(payload)
                cache.append({"judgment_id": f"AI-{sid}-{code}-{model['model_id']}", "segment_id": sid, "code": code,
                              "model_id": model["model_id"], "run_id": model["run_id"], "codebook_version": "0.2.0", "simulated": True,
                              "prompt_sha256": prompt_hash(lookup[sid], book, code), "raw_response": raw})
    corrections = [{"correction_id": "RETURN-001", "segment_id": "SYN-M01:0", "code": "concealed_reversal", "value": 0,
                    "participants": ["reader_a", "reader_b"], "context_quote": lookup["SYN-M01:1"]["text"],
                    "rationale": "All three simulated models recognized a concealment sequence but missed whose claim it was. The next paragraph explicitly rejects the rival's account. Under the existing stance criterion the passage is not the author's concealment story.",
                    "case_decision": "Reject SYN-M01 as a positive exemplar; retain it as a model-error and context-boundary case.",
                    "next_step": "Prospectively test wider context on new calibration material. Preserve this cache and this holdout; do not tune on their scores."}]
    inputs = {"codebook": "codebooks/v0.2.0.json", "previous_codebook": "codebooks/v0.1.0.json"}
    objects = {"campaigns": campaigns, "sources": sources, "segments": segments, "human_judgments": humans,
               "decisions": decisions, "revision": revision, "models": models, "model_judgments": cache, "corrections": corrections}
    for name, data in objects.items():
        inputs[name] = f"fixtures/synthetic/{name}.json"
        write(inputs[name], data)
    write("fixtures/synthetic/manifest.json", {"synthetic": True, "schema_version": 1, "fixture_version": "1.0.0",
          "generation": "scripts/build_synthetic_fixture.py; invented texts, readers, decisions and model responses",
          "codebook_version": book["version"], "inputs": inputs, "sha256": {p: digest((ROOT / p).read_bytes()) for p in inputs.values()}})
    print(f"Authored {len(segments)} synthetic segments and {len(cache)} simulated cached responses.")


if __name__ == "__main__":
    build()
