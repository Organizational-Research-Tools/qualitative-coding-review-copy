# Detailed rules behind the teaching example

For an overview, start with the [README](../README.md). For the real-data replay,
read [REAL_DATA_REPLAY.md](REAL_DATA_REPLAY.md). This page explains the designed
example's reference, voting and aggregation rules.


The method treats code development as collective interpretation. The team states
what a pattern means, offers rival readings and counterexamples, and records why
some instances are defensible. AI recognition is evaluated under that definition.
Aggregation creates a provisional guide to comparison. Returning to full cases
can change a label, challenge a proposed exemplar, identify a contextual failure,
or motivate a later codebook revision. It need not end by coarsening codes until
independent coding reliability rises.

## Progressive interpretation and the role of diagnostics

In the empirical study, adjudication across increasingly demanding pools was the
process that produced shared agreement. The objective is a vocabulary whose applications
can be defended through examples, contrasts, boundaries and reasons. Later pools
can expose weaknesses in earlier formulations. They need not yield monotonically
higher agreement, because both the material and the interpretation can change.

The empirical account distinguishes changed definitions, passage readings,
measurement rules and case interpretations, and marks where direct computation
ends and substantive reading begins. It uses original coding and adjudication as
authoritative before/after states where both survive.

AI is assessed for defensible applications of the developed interpretation.
Disagreement, false positives, false negatives and abstentions identify where
that application needs examination. An explicit collective decision is a reasoned
and revisable reference, not an infallible answer. Post-discussion agreement
records a resolution; it does not pretend to be another independent reading.

Aggregation moves from passages to campaign configurations under stated rules.
It does not change the categories simply to raise agreement, and it cannot itself
establish validity. Compare whether alternative gates, model subsets, vote rules
and defensible label corrections alter the case contrasts. Then read the cases to
explain why those differences matter. The existing empirical comparison requires a substantive explanation of those
contrasts, beyond successful pipeline execution.

## Separate kinds of judgment

| State | Meaning | Used as evaluation reference? |
|---|---|---|
| `collective` | At least two recorded perspectives plus an explicit defended decision | Yes |
| `adjudicated` | Explicit recorded resolution of a disputed reading | Yes |
| `single_coder` | One individual response | No |
| `unanimous_individual` | Multiple independent responses match, without recorded collective review | No |
| `unresolved` | Disagreement or uncertainty remains | No |
| `multiple_pools_require_resolution` | Multiple pools provide labels without an explicit resolution | No |
| `excluded` | Prepared unit is outside the task's substantive gate | No |
| `gate_uncertain` | Task applicability is unsettled | No |
| `no_reference` | No defended reference exists | No |

Raw records are versioned and immutable during a run. An explicit decision lists
its participants and the individual judgment IDs it addresses. Duplicate coding
keys are rejected; different pools cannot silently overwrite one another. The
reference layer retains every segment/code, including unresolved and excluded
ones. Case-return corrections apply to mapping campaigns only.

## Frozen evaluation

Campaigns, rather than segments, are assigned to calibration, holdout, or mapping.
The worked revision names calibration passages only; validation rejects any
holdout or mapping passage in that development list. Model cache records name
their simulated model, run, codebook version and exact prompt hash. Each parsed
vote must have a binary integer value and a quote found in the passage; `null`
means abstention. Malformed syntax or unsupported quotes are invalid responses.

These checks demonstrate the contracts; they cannot prove that real researchers
never saw or tuned on an evaluation pool. All chronology here was designed as
synthetic teaching data. An independent predictive-performance claim needs prospective freeze records,
complete training/prompt-development histories, and an untouched evaluation set.
Calibration and collective interpretation remain valuable without that claim. The demo
does not rank or choose rules by the holdout results.

## Vote rules

Let N be the number of selected models, y valid yes votes, and n valid no votes.
Missing, invalid and abstaining responses contribute to neither y nor n.

| Rule | Positive | Negative | Unresolved |
|---|---|---|---|
| `majority_fixed` | y > N/2 | n > N/2 | Otherwise |
| `unanimity_abstain` | y = N | n = N | Otherwise |
| `any_positive` | y >= 1 | n = N | Otherwise |
| `all_positive_indicator` | y = N, all responses valid | At least one no, all responses valid | Any invalid/missing/abstaining response |

The final rule measures whether a complete electorate unanimously recognizes an
instance. Its zero does not assert that the models agree on absence. In contrast,
`unanimity_abstain` abstains on disagreement. Both are provided because the source
evaluation and campaign-profile layers use different notions of unanimity.
The strict majority uses the expected electorate, including absent models in N;
a single surviving model cannot become a three-model majority.

## Evaluation and map denominators

For each code, model/rule and calibration/holdout split, export TP, FP, FN, TN,
unscored predictions, reference-state counts and defended-positive prevalence.
Precision, recall, F1 and accuracy are conditional on predictions that resolve
against defended references. Coverage is scored / defended. The additional
detected-fraction metric divides true positives by *all* defended positives,
including those whose predictions abstain. Undefined ratios are null, not zero.
These are diagnostic descriptions, not uncertainty estimates for an empirical
population. Collective references themselves can be challenged.

Profiles are separate for each campaign, code, rule and weighting:

- `share_resolved`: positive weight / resolved eligible weight.
- `coverage`: resolved eligible weight / all eligible weight.
- `lower_bound_eligible`: positive weight / all eligible weight.
- `upper_bound_eligible`: (positive + unresolved weight) / all eligible weight.

The interval is a missing-label sensitivity range, not a confidence interval.
It does not capture systematic model errors. Exclusions and uncertain gates are
reported separately and do not enter the eligible denominator. Thus gate error
is outside these bounds. An empirical application should also vary the gate.
Weights are either one per segment or the whitespace-delimited word count.
Neither substitutes for theoretical importance. Word weighting does not make
each word independent evidence and depends on the segmentation scheme.

## Reading and correction

Candidate roles derive from vote-rule sensitivity, unresolved labels/gates,
and the presence or absence of positive codes. The output prioritizes reading;
it estimates neither clusters nor causal effects. Segment IDs lead through the
lineage file to source IDs, Unicode character spans, paragraph indices, text
hashes and the exact cached judgments.

RETURN-001 documents an invented collective re-reading of SYN-M01. It overlays
a mapping label under the *existing* stance criterion, produces corrected
profiles, and changes the candidate role. It does not alter the codebook,
original responses or holdout metrics. A later prompt/context change would be
a new version evaluated on fresh material. Overlapping fictional windows are
flagged for joint reading, without claiming causal attribution.

## Scope of these contracts

The reference and frozen-evaluation contracts above describe the designed
synthetic workflow. The real-data replay works from frozen extracts of historical
records, which are less complete, and does not promote them into the same certified
reference states; [REAL_DATA_REPLAY.md](REAL_DATA_REPLAY.md) explains that boundary.
Reliability diagnostics are supporting evidence at a specified stage; no single
statistic substitutes for the interpretive and substantive argument.
