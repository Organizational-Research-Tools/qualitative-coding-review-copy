# Verification

## Repeat the checks

```sh
python3 -m unittest discover -s tests -v
python3 -m interpretive_map --output outputs/check-one
python3 -m interpretive_map --output outputs/check-two
python3 scripts/build_empirical_arc.py --output outputs/replay-one
python3 scripts/build_empirical_arc.py --output outputs/replay-two
python3 scripts/audit_artifact.py
```

Expected results:

- all 26 tests pass;
- the two synthetic runs and the two replay runs each produce byte-identical files;
- the replay prints `PASS` for 830 campaigns, 16 decisions and 5 cases;
- the audit reports `PASS`.

Generated outputs are ignored by Git.

## What the tests cover

- **Synthetic workflow:**
  - reference-state distinctions;
  - provenance;
  - duplicate and conflict handling;
  - gates;
  - missingness;
  - vote semantics;
  - coverage;
  - correction overlays;
  - frozen calibration and hold-out splits.

  These tests run with network and SQLite access blocked.
- **Real-data replay:**
  - number and label validation;
  - duplicate join keys;
  - mismatched campaign universes;
  - changed inputs;
  - paths that escape the input directory;
  - an end-to-end build from `data/empirical/` that is repeated and compared byte
    by byte.

## What the audit covers

The audit checks:

- the exact tracked-file allowlist;
- UTF-8 encoding and size limits;
- forbidden file types;
- personal absolute paths;
- email addresses;
- common credential shapes;
- that every Git remote is a GitHub repository.

It is a heuristic supplement to manual review, not a licensing clearance.

## Scope

These checks establish reproducible mechanics. They do not establish collective
validity, independent evaluation or causal effects. Those claims rest on the
research design described in the proposal and its technical appendix.
