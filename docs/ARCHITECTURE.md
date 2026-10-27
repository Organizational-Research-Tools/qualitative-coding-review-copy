# What each component contributes

The files fall into three roles: the runnable teaching example, the real-data
replay, and checks that protect the record.

## The teaching example: make the methodological steps visible

Run `python3 -m interpretive_map --output outputs/example`, then open the
resulting `review.html`. Everything on this path is invented. The output
filenames below are created in that output directory, not stored in Git.

| Question | Why the component exists | Implementation and input | Output to inspect |
|---|---|---|---|
| What changed in the interpretation, and why? | Keep the original disagreement beside the revised definition and decision | `codebooks/`, `fixtures/synthetic/revision.json`, `human_judgments.json`, `decisions.json`; [judgments.py](../interpretive_map/judgments.py) | `reference_states.json` and the code-development section of `report.md` |
| What exactly did a model see and answer? | Make context, prompt version and response traceable | [source_context.py](../interpretive_map/source_context.py), [prompts.py](../interpretive_map/prompts.py); authored `model_judgments.json` cache | `prompts.json`, `parsed_model_judgments.json` |
| Where does AI misapply the interpretation? | Inspect false positives, negatives and abstention with coverage | [voting.py](../interpretive_map/voting.py), [diagnostics.py](../interpretive_map/diagnostics.py) | `errors.csv`, `diagnostics.json` |
| How do passage judgments become a document comparison? | Expose denominators, vote rules, weighting and model dependence | [profiles.py](../interpretive_map/profiles.py) | `campaign_profiles.csv`, `model_subset_sensitivity.csv`, `case_candidates.json` |
| Can contextual reading change that comparison? | Apply an explicit correction while retaining the original map and raw responses | `fixtures/synthetic/corrections.json`; `apply_corrections()` in [profiles.py](../interpretive_map/profiles.py) | `campaign_profiles_after_reading.csv`, `case_candidates_after_reading.json` |
| Can a reader follow the entire example? | Assemble the same steps into a readable report with expandable source passages | [__main__.py](../interpretive_map/__main__.py) | `report.md`, `review.html`, `segment_lineage.json` |

The example contains two different changes: a codebook revision during
calibration, then a contextual label correction under the revised definition.
Only the latter changes the displayed map. Neither is an empirical estimate of
what the real trope revisions did to the real corpus.

## The real-data replay: the empirical study's joins, recomputed

[build_empirical_arc.py](../scripts/build_empirical_arc.py) reads the frozen
extracts in `data/empirical/` and rebuilds the walkthrough from adjudicated
decisions to case comparisons. [REAL_DATA_REPLAY.md](REAL_DATA_REPLAY.md)
describes the inputs, the checks and what the replay does not establish.

## Checks and maintenance

| Component | Purpose |
|---|---|
| [contracts.py](../interpretive_map/contracts.py) and the synthetic manifest | Reject changed inputs, inconsistent references, invalid spans and accidental use of evaluation material in the designed code-development step |
| `data/empirical/manifest.json` | Bind each real-data input to its SHA-256 hash; the replay refuses changed inputs |
| [tests/](../tests) | Check the mechanics with invented inputs; passing tests does not validate the empirical interpretation |
| [audit_artifact.py](../scripts/audit_artifact.py), `allowlist.txt` and `.gitignore` | Keep the tracked file inventory explicit and check common accidental disclosures |
| [build_synthetic_fixture.py](../scripts/build_synthetic_fixture.py) | Maintain the invented fixture; readers should run the example without rebuilding it |

## What is deliberately not here

This is not a packaged copy of the production research system. It omits report
collection, OCR, segmentation, the multi-user coding interface, provider clients,
paid inference, fine-tuning, batch services, market data, regressions and
clustering. Model votes are cached, so nothing here calls a model. The real-data
extracts carry identifiers, counts, labels and passage hashes, not report text,
coder identities or the research database.
