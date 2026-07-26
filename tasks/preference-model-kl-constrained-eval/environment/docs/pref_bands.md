# Preference evaluation bands

`schema_tag` must be `pref-eval-v1`.

## Tip fields

`beta` on every slice must match the durable tip selected from materials under
`/app/data/tips/`. Tip sheets kept beside the journal are operator mirrors and
are not the selection authority. Retired tip ids are not selected.

`tip_epoch` must match that same durable tip. A live high-beta tip is not the
graded selection.

## Slices

Each entry in `slices[]` has `id`, `win_rate`, `kl_to_ref`, `beta`, and
`tip_epoch`.

- `win_rate` is the mean soft pairwise win under the seated beta scale.
- `kl_to_ref` is the mean KL from the candidate token distributions to the
  reference distributions for that slice.

### Win-rate bands and KL ceilings

| slice id | win min | win max | kl ceiling |
| -------- | ------- | ------- | ---------- |
| s_alpha  | 0.68    | 0.76    | 0.12       |
| s_beta   | 0.60    | 0.70    | 0.15       |
| s_gamma  | 0.74    | 0.82    | 0.10       |
| s_delta  | 0.66    | 0.74    | 0.14       |

## eval_ok

`eval_ok` is true only when every graded slice satisfies its win-rate band and
KL ceiling and the tip fields match the durable selection. A surface win-rate
print from `/app/tools/prefprobe` is not sufficient.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/pref-eval.json`.
