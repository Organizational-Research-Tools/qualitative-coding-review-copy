# Schemas and provenance

JSON files use UTF-8. Hashes are SHA-256 over bytes unless the field names specify
text. These are executable contracts implemented in the linked modules, not
claims that a historical record contains evidence it never stored.

## Portable synthetic inputs

The manifest at [fixtures/synthetic/manifest.json](../fixtures/synthetic/manifest.json)
names and freezes every input, including both codebook versions. Normal runs do
not rebuild it. The [fixture builder](../scripts/build_synthetic_fixture.py) is an
explicit authoring operation, not an installation step.

| Record | Keys and important fields | Meaning |
|---|---|---|
| Campaign | `campaign_id`, `target_id`, `window`, `split`, `synthetic` | Split is calibration, holdout or mapping at campaign level; windows support overlap cautions. |
| Source | `source_id`, `campaign_id`, `text`, `sha256`, `synthetic` | Exact invented document text and hash. |
| Segment | `segment_id`, `campaign_id`, `source_id`, `start`, `end`, `text`, `text_sha256`, `source_paragraphs`, `gate`, `gate_reason` | Half-open Unicode character offsets into the source; gate is eligible, excluded or uncertain. |
| Human judgment | `judgment_id`, `segment_id`, `code`, `codebook_version`, `pool`, `coder`, `value`, `rationale` | Unique per segment/code/version/pool/coder. Values are integer 0/1 or null. Historical versions persist. |
| Defended decision | `decision_id`, segment/code/version, `kind`, `value`, `participants`, `judgment_ids`, `rationale` | At least two perspectives, matching references and an explicit collective/adjudicated decision. |
| Revision | `from_version`, `to_version`, `development_segments`, discussion/decision/sequence | Development passages must be from calibration campaigns. |
| Model | `model_id`, `run_id`, `simulated` | Invented model identity; simulated must be true. |
| Cached judgment | `judgment_id`, segment/code/model/run/version, `prompt_sha256`, raw response | Unique model vote per segment/code; exact prompt binding checked when parsed. |
| Correction | `correction_id`, segment/code/value, participants/rationale/context quote | Mapping-only overlay. The quoted context must occur in the source; raw model responses are unchanged. |

See [contracts.py](../interpretive_map/contracts.py) for validation and
[voting.py](../interpretive_map/voting.py) for the response parser. Invalid syntax,
missing response, abstention and valid negative response have distinct meanings.
A matching quotation establishes textual provenance, not interpretive correctness.

## Portable outputs

| Output | Record grain and use |
|---|---|
| `reference_states.json` | Segment × code: state/value and raw judgment/decision links. Only defended decisions have evaluation values. |
| `parsed_model_judgments.json`, `prompts.json` | Parsed cache status and exact constructed prompts. |
| `diagnostics.json`, `errors.csv` | Split × code × model/rule counts, conditional metrics, coverage and errors against defended references. |
| `campaign_profiles.csv` | Campaign × code × rule × weighting, including eligible/resolved/positive/unknown counts and weights, exclusions, uncertain gates and lineage. |
| `model_subset_sensitivity.csv` | Same profile grain with each model omitted in turn. |
| `segment_lineage.json` | Vote row plus judgment links, source span/hash and synthetic text. |
| `case_candidates.json` | Mapping campaign reading priorities, overlapping campaigns and segment IDs. No estimated cluster membership. |
| `consensus_after_reading.json`, `campaign_profiles_after_reading.csv`, `case_candidates_after_reading.json` | Explicit overlay and its analytical consequences. |
| `run_manifest.json`, `environment.json` | Frozen input, code and output hashes; runtime recorded separately. |

`share_resolved = positive_weight / resolved_weight` and
`coverage = resolved_weight / eligible_weight`. Bounds assign each unresolved
eligible vote 0 or 1. Excluded/uncertain gates remain outside that denominator and
are reported separately. Empty denominators yield null. Bounds are not confidence
intervals and do not account for systematic misinterpretation. Full rule and
reference-state definitions are in [METHOD.md](METHOD.md).
