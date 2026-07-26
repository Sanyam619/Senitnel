# Desk notes

The mixture-of-experts evaluation desk loads expert capacity sheets under
`/app/data/experts/`, router tip state under `/app/data/routers/`, and
per-slice logit rows under `/app/data/eval/`.

Router tip selection and hold membership are governed by the router materials
in that tree. Tip sheets kept as mirrors for operator probes are not the
selection authority. Held experts stay in the roster with zero mass; they are
not deleted from the expert array.

## Evaluation selection

The desk ships under trial evaluation selection. While selection stays on
trial, every engine build refreshes the seating surfaces from the desk seed
set, so surface edits alone do not stick across builds. Serving selection
requires the evaluation preference under `/app/calib/` to name serving and a
tip binding receipt under the same tree that matches the selected durable tip
identity. A mismatched or missing binding keeps trial refresh behavior.

`/app/tools/moeprobe` prints a coarse balance line based on share spread.
It does not certify deep evaluation health.
