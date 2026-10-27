# Replay the real example from coding to case comparison

The teaching example uses invented material. This replay uses the empirical
study's own records, frozen as extracts in `data/empirical/`, and recomputes the
joins behind the proposal's proof of concept: from adjudicated passage decisions,
through campaign profiles, to the cases selected for close reading.

## Run it

From the repository root, with Python 3.11 or later and no other packages:

```sh
python3 scripts/build_empirical_arc.py --output outputs/replay
```

Open `outputs/replay/index.html` or `WALKTHROUGH.md`, then the JSON files beside
them. The command prints `PASS` with 830 campaigns, 16 decisions and 5 cases.
Choose a new output name for each run; the builder refuses to overwrite.

## What it connects

| Question | Input in `data/empirical/` | Work performed |
|---|---|---|
| What changed in a reading? | Original labels, adjudicated codes, cached model values and passage hashes for 16 selected decisions | Preserve the before/after distinction, including missing original states |
| What recurs across reports? | Campaign trope profiles, narrative numerator and denominator, stored cluster vectors | Check the common campaign universe; recompute breadth, prevalence and trope pairs |
| Why compare these cases? | Versioned comparison-matrix rows | Join case IDs while keeping the different narrative measures and environment tiers |
| How are rhetorical resources related? | Five authored case cards | Present close readings as supplied evidence; counts do not generate strategies |
| What does a return to the text change? | Selected adjudications and the frozen correction overlay | Recompute the bounded numerical consequences while preserving cached outputs |

## Checks

The builder verifies every input against `data/empirical/manifest.json` before
and after reading, rejects duplicate join keys and mismatched campaign
universes, checks stored cluster features, and writes a manifest of input,
builder and output hashes. Repeating a build produces byte-identical files.

## What the replay does not establish

- **No source text.** Passages are represented by SHA-256 hashes and lengths, not
  text. The replay shows which readings changed and how, not the passages
  themselves.
- **Interpretations are inputs.** The five case cards are close readings written
  by the researchers. The program presents them beside the computed joins; it
  does not derive them. Focused, modular and integrated strategies are
  interpretive results of comparison, not clusters recovered by this script.
- **No refits or model calls.** Cluster assignments are retained as stored;
  nothing is re-estimated, recoded or re-run.
- **Historical records are less complete than the teaching contracts.** The
  extracts do not promote historical labels into the certified reference states
  described in [METHOD.md](METHOD.md).
