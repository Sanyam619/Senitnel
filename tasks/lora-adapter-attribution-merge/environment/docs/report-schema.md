# merge-report.json schema

The pipeline writes a single JSON object to `/output/merge-report.json`.
It has three top-level sections plus a `schema_tag`.

## schema_tag

Exactly the string `lora-merge-v1`.

## adapters

An array. One entry per adapter label. Each entry is an object with:

| field              | type   | meaning                                                                                            |
| ------------------ | ------ | -------------------------------------------------------------------------------------------------- |
| `label`            | string | Adapter label (`alpha`, `beta`, `gamma`, `delta`).                                                 |
| `source_snapshot`  | string | The base snapshot the adapter was originally fit against (`S1`, `S2`, or `S3`).                    |
| `target_snapshot`  | string | The base snapshot the adapter's effective delta is now expressed against (`S3` for this pipeline). |
| `rebased_norm`     | number | Frobenius norm of the adapter's full effective delta after rebasing to `target_snapshot`.          |
| `contribution_norm`| number | Frobenius norm of that adapter's share of the merged state.                                        |

Both `rebased_norm` and `contribution_norm` are non-negative finite doubles.

## evaluation

An array. One entry per downstream task under `/app/data/eval/`.
Each entry is an object with:

| field                  | type          | meaning                                                                                                                    |
| ---------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `task_id`              | string        | Downstream task identifier (`task_1` .. `task_5`).                                                                         |
| `baseline_score`       | number        | Score under `S3` with no adapter delta applied.                                                                            |
| `merged_score`         | number        | Score under `S3` with the merged delta applied.                                                                            |
| `decommission_scores`  | object        | Map `label -> number`; the score obtained when that adapter's contribution is subtracted from the merged state.            |

The scoring convention is `score = -mean_squared_error`; higher is better.
The evaluator tolerance for "no regression" and for "decommission recovers baseline" is `1e-8` in absolute score units.

## attribution

An object with:

| field                                     | type   | meaning                                                                              |
| ----------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| `total_delta_frobenius`                   | number | Frobenius norm of the full merged delta tensor.                                      |
| `sum_per_adapter_frobenius_squared`       | number | Sum of squared Frobenius norms of the four per-adapter contributions.                |
| `residual_after_all_decommission`         | number | Frobenius norm of the residual after subtracting every per-adapter contribution.     |

`residual_after_all_decommission` must be `<= 1e-9`.
Note: `sum_per_adapter_frobenius_squared` is NOT expected to equal `total_delta_frobenius^2`
in general — the per-adapter contributions are not required to be mutually orthogonal.
