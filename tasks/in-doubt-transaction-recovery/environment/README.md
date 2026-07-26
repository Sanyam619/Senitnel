Ops recovery console layout:

- `/app/ops/tools/replay.sh` is the staged journal replay pipeline the console invokes.
- Stage helpers live beside that pipeline and are named only in the shell script it runs.
- `/app/ops/runbooks/recovery_policy.md` documents recovery vocabulary used by the helpers.
- `scenarios/<name>/meta.properties` lists member names and a mode token for that drill.
- `scenarios/<name>/coordinator.log` holds flushed global rows (`TX <id> DECISION COMMIT|ABORT`).
- `scenarios/<name>/member-<name>.log` holds per-member rows (`TX <id> PREPARED|COMMITTED|ABORTED`).
- `scenarios/<name>/saga.plan` binds saga ids to transaction ids and lists step states with undo labels.

Run from `/app`. Entry point: `com.acme.ops.Console`. Artifacts land under `/app/output`.

Output nesting:

- `decisions.json`: `{"scenarios":{"<drill>":{"transactions":{"<tx>":{"decision":"COMMIT"|"ABORT"}}}}}`
- `compensations.json`: `{"scenarios":{"<drill>":{"sagas":{"<saga>":{"actions":["<label>",...]}}}}}`

Every drill directory name must appear in both artifacts. The set of transaction ids under a drill must be the union of every tx id seen in that drill's coordinator journal, member journals, **and every tx id bound by a `SAGA` line in the drill's `saga.plan`** — a saga-bound transfer with no journal evidence is still an in-doubt unit that owes a decision. Every saga id from the saga plan must appear under sagas; a saga whose bound transfer commits keeps the entry with an empty actions array.
