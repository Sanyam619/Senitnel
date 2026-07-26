# Calibration notes

The continual-learning evaluation driver loads task fixtures under
`/app/data/tasks/` and replay-buffer tip state under `/app/data/replay/`.

Tip selection and the replay fraction applied during scoring are governed
by the replay materials in that tree. Tip sheets kept as mirrors for
operator probes are not the selection authority. Stratum hold and release
rows are epoch-scoped against the selected tip; a flat roster beside them
is not.

## Evaluation selection

The driver ships under trial evaluation selection. While selection stays on
trial, or the tip binding receipt under `/app/calib/` does not match the
selected durable tip, every engine build refreshes the seating surfaces from
the desk seed set, so surface edits alone do not stick across builds.

`/app/tools/clprobe` prints a coarse status line based on the last task's
accuracy. It does not certify deep evaluation health.
