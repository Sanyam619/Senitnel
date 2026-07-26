# Evaluation notes

The mixture-of-depths evaluation loads frozen checkpoints under
`/app/data/ckpt/`, router tip state under `/app/data/routers/`, and
per-scenario token rows under `/app/data/eval/`.

Router tip selection and routing capacity are governed by the router
materials in that tree. Tip sheets kept as mirrors for operator probes are
not the selection authority. Depth schedule sheets under the router tree
drive average routed depth; ledger mirrors of those sheets are not
authoritative.

## Evaluation selection

The evaluation ships under trial selection. While selection stays on
trial, every rebuild of the evaluation engine restores the evaluation
sources from the trial seed set, so source edits alone do not stick across
rebuilds. Serving selection requires the evaluation preference under
`/app/calib/` to name serving and a tip binding record under the same tree
that matches the selected durable tip identity, epoch, and capacity. A
mismatched or missing binding keeps trial refresh behavior.

`/app/tools/modprobe` prints a coarse depth line based on mean token score
spread. It does not certify deep evaluation health.
