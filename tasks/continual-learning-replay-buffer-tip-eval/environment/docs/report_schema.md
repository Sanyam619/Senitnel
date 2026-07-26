# cl-eval.json field reference

This note describes the shape of `/output/cl-eval.json` for readers who
land here from the calibration notes; it is not a substitute for the
evaluation bands document.

| field | type | notes |
| ----- | ---- | ----- |
| `schema_tag` | string | always `cl-eval-v1` |
| `tasks` | array | one entry per task fixture, in curriculum order |
| `tasks[].id` | string | task fixture id |
| `tasks[].accuracy` | number | scored accuracy for that task |
| `tasks[].forgetting` | number | drop from that task's peak accuracy |
| `tasks[].replay_frac` | number | replay fraction applied during scoring |
| `tasks[].tip_epoch` | integer | epoch of the replay-buffer tip in force |
| `eval_ok` | boolean | overall run health |
