# Read one complete worked example

This invented example makes the paper's workflow visible. It is separate from
[the real-data replay](REAL_DATA_REPLAY.md). Its
`concealed_reversal` teaching code is not a historical version of shaky foundations.

## Run the example


Use Python 3.11 or newer. There are no third-party dependencies or inference
clients. All commands below run from the repository root. No source project is
needed for the synthetic exercise.

An optional isolated environment is:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

There is nothing to install with pip. Running as a module from the checkout is the
supported interface. Keep the checkout and its fixtures together.

## Run and verify

```sh
python3 -m unittest discover -s tests -v
python3 -m interpretive_map
python3 scripts/audit_artifact.py
```

The demo refuses to overwrite `outputs/demo`. If that path already exists, keep
it and use a new name:

```sh
python3 -m interpretive_map --output outputs/second-run
```

The CLI prints `SYNTHETIC OFFLINE DEMO COMPLETE` and these counts:

| Item | Expected |
|---|---:|
| Campaigns / segments | 6 / 16 |
| Individual judgments / collective decisions | 33 / 12 |
| Simulated responses | 82 |
| Campaign profile rows / subset profile rows | 96 / 288 |
| Reading candidates | 3 |

Open the generated `report.md` and `review.html` in the output directory. The HTML
is self-contained and has expandable passages, with no scripts or external assets.
[VERIFICATION.md](VERIFICATION.md) records the test count and checked interpreter.

## What to read in the output

Begin with `review.html`: its narrative report connects the steps, and its
expandable passages let you inspect the context. Use the files below to follow
specific parts of the paper's argument.

| Output | Question to ask | Connection to the paper |
|---|---|---|
| `reference_states.json` | Is this an individual response, a matching response or an explicit defended decision? | Interpretation is not reducible to label agreement |
| `errors.csv` and `diagnostics.json` | Which mistakes survive model agreement, and how many cases remain unresolved? | AI application needs error inspection and coverage |
| `campaign_profiles.csv` and `model_subset_sensitivity.csv` | Which differences depend on vote rule, denominator or model choice? | The corpus map is a provisional guide to comparison |
| `campaign_profiles_after_reading.csv` and `case_candidates_after_reading.json` | What changes when the context challenges the first reading? | Return to text has a recorded analytical consequence |
| `segment_lineage.json` and `run_manifest.json` | Which passage, responses and frozen inputs produced this result? | A reader can audit how the conclusion was reached |

These are explanatory aids, not separate contributions or additional empirical
results. You can follow the exercise in the HTML before opening the JSON files.

## Follow one full interpretive cycle

1. Read [revision.json](../fixtures/synthetic/revision.json) and the two codebooks
   [v0.1](../codebooks/v0.1.0.json) and [v0.2](../codebooks/v0.2.0.json). A broad
   reversal reading is challenged by a delayed launch that lacks concealment and
   revelation. The revised definition specifies a mechanism and author stance.
   The disagreement persists as earlier-version judgments.
2. Inspect [human_judgments.json](../fixtures/synthetic/human_judgments.json) and
   [decisions.json](../fixtures/synthetic/decisions.json). Identify the perspectives,
   rationale and linked decision; matching labels alone are not that record.
3. Inspect the generated `reference_states.json` and `errors.csv`. The illustrative
   holdout includes a unanimous false positive. For `concealed_reversal`, strict
   majority gives TP/FP/FN/TN = 1/1/0/1 with 3/3 predictions resolved. Unanimity
   with abstention gives 0/1/0/1 with 2/3 resolved. Those are invented diagnostics.
4. In `campaign_profiles.csv`, locate SYN-M01, `concealed_reversal`,
   `majority_fixed`, `segment`. Its initial share is 1/2. Find the contributing
   segment in `segment_lineage.json`, then read both passages in `review.html`.
   The first quotes a rival allegation; the next rejects it.
5. Read [corrections.json](../fixtures/synthetic/corrections.json). The explicit
   RETURN-001 overlay changes the share to 0/2 and removes the proposed positive
   exemplar role in `case_candidates_after_reading.json`. The incomplete third
   passage stays gate-uncertain; it is not counted as a negative.
6. Compare the original and corrected profile files. The original response cache,
   codebook and holdout diagnostics are unchanged. The analytical consequence is
   visible without rewriting the evidence that led to the initial suggestion.

The early codebook revision and the later correction are different operations:
the first changes a definition, while the second corrects an application under
the existing definition. The exercise ends with a corrected orientation for reading, not a completed
empirical explanation. For a real case, explain why the contextual distinction
matters to the comparative argument.

## Repeatability and expected failures

The unit suite repeats synthetic computation with network and SQLite access
blocked and compares every generated byte. The real-data replay is a separate
check described in [REAL_DATA_REPLAY.md](REAL_DATA_REPLAY.md).

A fixture hash mismatch means an input changed without an intentional new freeze.
A reused output-directory error protects history. Unknown response formats and
insufficient model quorums remain unresolved. An audit inventory failure means a
file was added without updating `allowlist.txt`, or the allowlist names a missing
file. Do not bypass these checks by deleting old results or relaxing provenance.

Fixture authoring is a maintenance operation: edit the synthetic recipe, rebuild
intentionally, inspect the changed inputs/hashes, and rerun tests.
