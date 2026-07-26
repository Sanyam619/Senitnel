# Report schema and metric definitions

`spec-eval eval` writes a single JSON object with `schema_tag = "spec-calib-v1"`.
The object contains a per-slice array, a per-entropy-bucket breakdown, and
a summary block.

## Per-slice fields

Each entry in `slices[]` carries these fields:

- `slice_id`                 : one of `num_completion`, `repetition_prose`,
                                 `low_entropy_json`, `code_rare_tokens`
- `positions`                : integer count of decoded positions
- `ks_statistic`             : max abs difference between the CDF of emitted
                                 tokens and the CDF of the reference tokens
                                 across the vocabulary (Kolmogorov-Smirnov
                                 statistic; lower is closer to reference)
- `accept_rate`              : fraction of positions where the draft-side
                                 proposal was accepted by the acceptance
                                 boundary (before any fallback)
- `divergence_rate`          : fraction of positions whose emitted token
                                 differs from the reference token
- `speedup`                  : effective step gain vs. non-speculative
                                 decoding on this slice, `1 + accept_rate`
- `fallback_rate`            : fraction of positions that consumed the
                                 target's argmax directly rather than any
                                 draft or residual token
- `low_entropy_accept_rate`  : `accept_rate` restricted to positions with
                                 fixture entropy below the low-entropy
                                 threshold (`codebook_stats.low_entropy_threshold`)
- `high_entropy_accept_rate` : `accept_rate` restricted to positions at or
                                 above the low-entropy threshold
- `mean_draft_target_tv`     : mean total-variation distance between the
                                 calibrated draft distribution and the
                                 target distribution across positions in
                                 the slice (`0.5 * sum |p_t - p_d|`). A
                                 value of zero means the draft side is a
                                 perfect copy of the target — which is not
                                 a valid calibration.

## Positions block

`positions.low_entropy` and `positions.high_entropy` each carry `count`,
`accept_rate`, and `fallback_rate` aggregated across all slices.  The
entropy boundary between the two buckets is
`codebook_stats.low_entropy_threshold`.

## Summary block

`summary.overall_speedup`, `summary.overall_divergence`,
`summary.overall_fallback_rate` are pooled across every emitted position.
`summary.all_slices_pass` is a boolean self-check that the runner sets
according to the pipeline's internal thresholds; the verifier does not
depend on this flag and computes its own pass criteria from the numeric
fields above.

## Health bands used by the verifier

These are the numeric bands the report must satisfy after a successful
recalibration (derived from the same fields above):

- every slice: `ks_statistic <= 0.10`, `accept_rate >= 0.75`,
  `divergence_rate <= 0.10`, `0.003 <= mean_draft_target_tv <= 0.06`,
  and `fallback_rate <= 0.15`
- tighter slices: `num_completion` and `low_entropy_json` keep
  `ks_statistic <= 0.05` and `divergence_rate <= 0.05`;
  `code_rare_tokens` keeps `ks_statistic <= 0.08`,
  `divergence_rate <= 0.08`, and `accept_rate >= 0.80`
- per-slice entropy: every slice must keep
  `high_entropy_accept_rate >= 0.80`
- pooled: `summary.overall_speedup >= 1.60` and `< 2.0`,
  `summary.overall_divergence <= 0.075`,
  `summary.overall_fallback_rate <= 0.20`
- entropy buckets: `positions.low_entropy.accept_rate >= 0.85` and
  `positions.high_entropy.accept_rate >= 0.85`

## Reproducibility

A fresh `cargo build --release --offline --locked` from the same
sources must produce a binary that emits bit-identical metrics (to
within `1e-9` tolerance) when run with the same seed and data.  This
is verified by rebuilding the crate and comparing the resulting report
field by field — including the per-slice metrics AND the summary and
positions blocks — against the originally submitted report.

## Anti-tamper via probe events

Because `spec-eval probe --slice X --seed S` emits one line per position
with the emitted token, reference token, accept / fallback flags, and
per-position `draft_target_tv`, any consumer can reconstruct
`accept_rate`, `fallback_rate`, `divergence_rate`, and
`mean_draft_target_tv` for that slice from the probe stream and
cross-check them against the fields the runner wrote into the aggregate
report on the same seed. A report whose per-slice metrics disagree with
the probe reconstruction has been hand-edited.
