Journal Formats
===============

Coordinator and participant streams are JSON Lines (one object per line).
Field names observed in exports include `tag`, `epoch`, `ts`, `lab`,
`volume_id`, and free-form `msg` on participant notes.

Crash-export supporting records under `/app/data/episodes/<name>/`:

- `volume_seal.json` — sealed volume lineage metadata
- `leases.json` — federation claim list snapshot from the abort window
- `quarantine.json` — peer gate map snapshot
- `fragments.json` — ordered part descriptors with hex payloads
- `shelves/<key>/payload.bin` — shelf bytes also copied into
  `/var/lib/fleet/volumes/` at image build

Ops journal (`/var/lib/fleet/ops/journal.jsonl`) rows include `tag`
(`cutover` / `rollback`), `gen`, `mode`, and `hold`. Sealed cutover for
the target generation is authoritative over provisional rollback rows.

Vocabulary split (do not conflate):

- Journal / `attach.intent` mode token: `seal` or `decoy`
- Volume subdirectory / `PAYLOAD_LINEAGE`: `sealed` or `decoy`
  (`seal` is not a directory under `volumes/<episode>/`)
- Cutover receipt `/var/lib/fleet/state/cutover.ok`: `key=value` lines
  (`gen=…`, `hold=…`, `mode=seal`), not a JSON object
- Suppressing abort rematerialize means skip copying abort.d onto the live
  drop-in when the receipt matches — keep `/etc/fleet/reconcile.d/90-local.conf`
  present and site-standard; deleting that drop-in is not suppression.
  Leave `/var/lib/fleet/ops/abort.d/90-local.conf` with its abort-window
  synonym tokens; rewriting that abort package is not the recovery action

Epoch cutoff and borrow selection follow the reconciliation contract.
Exact outcomes also depend on drop-in fold, abort rematerialize vs durable
cutover receipt, generation alignment, holds, and same-inode sealed
attaches under the live trees.
