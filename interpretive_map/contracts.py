"""Strict, read-only input validation and content-addressed provenance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def unique(rows, fields):
    result = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        if key in result:
            raise ValueError(f"Duplicate {fields}: {key}; resolve explicitly, never overwrite")
        result[key] = row
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_bundle(root: Path):
    manifest = json.loads((root / "fixtures/synthetic/manifest.json").read_text())
    require(manifest["synthetic"] is True, "Only the synthetic demonstration is supported")
    for name, checksum in manifest["sha256"].items():
        path = root / name
        require(path.resolve().is_relative_to(root.resolve()), "Manifest path escapes root")
        require(digest(path.read_bytes()) == checksum, f"Frozen input hash mismatch: {name}")
    bundle = {name: json.loads((root / path).read_text()) for name, path in manifest["inputs"].items()}
    bundle["manifest"] = manifest
    validate_bundle(bundle)
    return bundle


def validate_bundle(b):
    campaigns = unique(b["campaigns"], ("campaign_id",))
    sources = unique(b["sources"], ("source_id",))
    segments = unique(b["segments"], ("segment_id",))
    codebook = b["codebook"]
    codes = set(codebook["codes"])
    versions = {b["previous_codebook"]["version"], codebook["version"]}
    for c in campaigns.values():
        require(c["split"] in {"calibration", "holdout", "mapping"}, "Unknown split")
        require(c["synthetic"] is True, "Non-synthetic campaign")
    for s in sources.values():
        require(s["synthetic"] is True and s["sha256"] == digest(s["text"]), "Source provenance mismatch")
    for s in segments.values():
        require((s["campaign_id"],) in campaigns, "Unknown campaign")
        source = sources[(s["source_id"],)]
        require(source["campaign_id"] == s["campaign_id"], "Source/campaign mismatch")
        require(type(s["start"]) is int and 0 <= s["start"] < s["end"] <= len(source["text"]), "Invalid span")
        require(source["text"][s["start"]:s["end"]] == s["text"], "Segment text/span mismatch")
        require(s["text_sha256"] == digest(s["text"]), "Segment hash mismatch")
        require(s["gate"] in {"eligible", "excluded", "uncertain"}, "Unknown gate")
        require(bool(s["gate_reason"]), "Gate needs a rationale")
    judgments = unique(b["human_judgments"], ("judgment_id",))
    unique(b["human_judgments"], ("segment_id", "code", "codebook_version", "pool", "coder"))
    for j in judgments.values():
        require((j["segment_id"],) in segments and j["code"] in codes, "Unknown judgment key")
        require(j["codebook_version"] in versions, "Unknown judgment version")
        require(j["value"] is None or type(j["value"]) is int and j["value"] in (0, 1), "Invalid human label")
        require(bool(j["rationale"]), "Human rationale required")
    unique(b["decisions"], ("decision_id",))
    unique(b["decisions"], ("segment_id", "code", "codebook_version"))
    for d in b["decisions"]:
        require(d["codebook_version"] == codebook["version"], "Decision/version mismatch")
        require(type(d["value"]) is int and d["value"] in (0, 1), "Decision must be binary")
        require(len(set(d["participants"])) >= 2 and bool(d["rationale"]), "Collective decision needs participants and rationale")
        require(d["kind"] in {"collective", "adjudicated"}, "Unknown collective decision kind")
        refs = [judgments[(ref,)] for ref in d["judgment_ids"]]
        require(len({j["coder"] for j in refs}) >= 2, "Decision requires at least two raw perspectives")
        require(all(j["coder"] in d["participants"] for j in refs), "Decision participants mismatch")
        require(all((j["segment_id"], j["code"], j["codebook_version"]) == (d["segment_id"], d["code"], d["codebook_version"]) for j in refs), "Decision references mismatch")
    require(b["revision"]["from_version"] == b["previous_codebook"]["version"] and b["revision"]["to_version"] == codebook["version"], "Revision versions mismatch")
    for sid in b["revision"]["development_segments"]:
        s = segments[(sid,)]
        require(campaigns[(s["campaign_id"],)]["split"] == "calibration", "Holdout/mapping used for development")
    unique(b["models"], ("model_id",))
    models = {m["model_id"] for m in b["models"]}
    run_ids = {m["model_id"]: m["run_id"] for m in b["models"]}
    require(all(m["simulated"] is True for m in b["models"]), "Only simulated model cache permitted")
    unique(b["model_judgments"], ("judgment_id",))
    unique(b["model_judgments"], ("segment_id", "code", "model_id"))
    for j in b["model_judgments"]:
        require(j["model_id"] in models and j["code"] in codes, "Unknown model/code")
        require(j["run_id"] == run_ids[j["model_id"]], "Model/run mismatch")
        require((j["segment_id"],) in segments, "Unknown cached segment")
        require(j["codebook_version"] == codebook["version"] and j["simulated"] is True, "Cache provenance mismatch")
    unique(b["corrections"], ("segment_id", "code"))
    for c in b["corrections"]:
        s = segments[(c["segment_id"],)]
        require(campaigns[(s["campaign_id"],)]["split"] == "mapping", "Return-to-text corrections cannot change evaluation labels")
        require(c["code"] in codes and type(c["value"]) is int and c["value"] in (0, 1), "Invalid correction")
        require(len(set(c["participants"])) >= 2 and bool(c["rationale"]), "Correction needs collective rationale")
        source = sources[(s["source_id"],)]
        require(c["context_quote"] in source["text"], "Correction quote does not occur in source")
