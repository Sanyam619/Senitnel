# Report Schema — `warmup-report-1`

The host writes `/output/warmup-report.json`.

## Top level

| field            | type    | notes                            |
| ---------------- | ------- | -------------------------------- |
| `schema_version` | string  | constant `warmup-report-1`       |
| `registry_epoch` | integer | equals manifest `epoch`          |
| `scenarios`      | array   | one row per scenario, **sorted by `id` ascending** |

## Row fields

| field                 | type   | notes |
| --------------------- | ------ | ----- |
| `id`                  | string | scenario id |
| `outcome`             | string | `promoted`, `held`, or `refused` |
| `host_call_permitted` | bool   | host crossing allowed |
| `category`            | string | closed token (below) |
| `checks_installed`    | list   | guard set for the row |

## Category vocabulary (closed set)

- `interpreter_only`
- `held_polymorphic`
- `type_bypass_blocked`
- `arity_bypass_blocked`
- `bounds_bypass_blocked`
- `table_bypass_blocked`
- `benign_type_stable`
- `benign_table_stable`
- `benign_epoch_bumped`

`*_unclassified` must not appear in a repaired report.

## Guard binding

| category | `checks_installed` |
| -------- | ------------------ |
| `interpreter_only` | `[]` |
| `held_polymorphic` | exactly `["type"]` |
| `*_bypass_blocked` | all four: `type`, `arity`, `bounds`, `table` |
| `benign_epoch_bumped` | all four |
| `benign_type_stable` / `benign_table_stable` | `[]` |

Admission precedence and decision rules are defined in
`/app/docs/authority-notes.md`. Running the host twice must keep the same
epoch and decisions.
