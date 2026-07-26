# Continual-learning evaluation bands

`schema_tag` must be `cl-eval-v1`.

## Tip resolution

`tip_epoch` and `replay_frac` for every task row must match the selected
durable replay-buffer tip drawn from materials under `/app/data/replay/`.
Tip sheets kept beside the journal are operator mirrors and are not the
selection authority. Retired tip ids are not selected.

When the eval driver is pointed at an alternate data root that still carries
journal and task fixtures, every task row's `tip_epoch` and `replay_frac`
must still follow that root's journal-resolved sealed tip. Preference and
binding under `/app/calib/` seat rebuild durability; they do not replace the
journal-resolved replay fraction on those reports.

## Strata holds

Replay strata attach to task fixtures. Hold and release state is
epoch-scoped against the selected tip. Coarse roster summaries are
operator conveniences and are not authoritative. A held stratum does not
receive durable replay boost for tasks seated on it.

## Tasks

Each entry in `tasks[]` has `id`, `accuracy`, `forgetting`, `replay_frac`,
and `tip_epoch`.

- `replay_frac` and `tip_epoch` are identical across every task row.
- `forgetting` is never negative.
- Task fixtures under `/app/data/tasks/` participate in scoring. An
  archived scoring sample from a healthy pass is kept under
  `/app/data/tasks/audit/` for calibration reference.

### Accuracy bands

| task id | min | max |
| ------- | --- | --- |
| t_alpha | 0.770 | 0.790 |
| t_beta  | 0.690 | 0.710 |
| t_gamma | 0.710 | 0.730 |
| t_delta | 0.772 | 0.792 |

### Forgetting bands

| task id | min | max |
| ------- | --- | --- |
| t_alpha | 0.010 | 0.030 |
| t_beta  | 0.050 | 0.070 |
| t_gamma | 0.000 | 0.020 |
| t_delta | 0.000 | 0.010 |

## eval_ok

`eval_ok` is true only when every task's accuracy lands inside its band and
the run's internal invariants hold. A shallow print from `/app/tools/clprobe`
is not sufficient evidence of a healthy run.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/cl-eval.json`.
