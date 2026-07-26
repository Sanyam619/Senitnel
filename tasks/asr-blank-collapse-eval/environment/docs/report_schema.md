# Evaluation report schema

`/output/asr-eval.json` is a single JSON object.

| field | type | meaning |
| --- | --- | --- |
| `schema_tag` | string | report revision, currently `asr-eval-v3` |
| `slices` | array | one entry per required slice, in the published order |
| `eval_ok` | boolean | every published slice is inside its band |

Each entry of `slices` is an object:

| field | type | meaning |
| --- | --- | --- |
| `id` | string | slice id from the published band table |
| `wer` | number | word error rate over the slice, in `[0, 1]` |
| `cer` | number | character error rate over the slice, in `[0, 1]` |
| `blank_mode` | string | decode path the run used, `ctc_collapse` or `rnnt_join` |
| `lm_weight` | number | shallow-fusion weight the run used during search |
| `tip_epoch` | integer | decoder registry generation the run was scored under |

`wer` and `cer` are ratios over the whole slice: summed edit distance over
summed reference length, words for `wer` and characters of the space-joined
reference for `cer`. They are not per-utterance averages.

`blank_mode`, `lm_weight`, and `tip_epoch` describe the configuration the run
actually decoded with. They are report fields, not switches: writing a value
that the run did not decode under makes the report inconsistent with the
metrics beside it.

`eval_ok` is a claim about this report only. It is true when all six published
slices are inside both of their bands.
