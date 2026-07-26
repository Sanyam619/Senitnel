# Evaluation report schema

`/output/prune-eval.json` is a single JSON object.

| field | type | meaning |
| --- | --- | --- |
| `schema_tag` | string | report revision, currently `prune-eval-v2` |
| `scenarios` | array | one entry per required scenario, in the published order |
| `bands_ok` | boolean | every published scenario is inside its bands |

Each entry of `scenarios` is an object:

| field | type | meaning |
| --- | --- | --- |
| `id` | string | scenario id from the published band table |
| `accuracy` | number | share of the slice's marks the pruned stack reproduces, in `[0, 1]` |
| `sparsity` | number | parameter share the surviving stack drops |
| `flops_frac` | number | multiply share the surviving stack keeps |
| `mask_tip` | integer | registry generation of the channel roster the run survived on |

`accuracy` is counted over the whole slice: rows whose winning class equals the
mark the slice carries, divided by the number of rows. It is not an average of
per-batch rates.

`sparsity`, `flops_frac` and `mask_tip` describe the roster the run was actually
scored on. They are report fields, not switches: writing a generation the run
did not survive on makes the report inconsistent with the accuracy beside it.

`bands_ok` is a claim about this report only. It is true when all six published
scenarios are inside their accuracy band and inside both geometry bands.
