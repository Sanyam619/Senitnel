Seating Contract
================

Graded seating produces `/output/autofs-seat.json`:

- `schema_tag` must be the literal string `autofs-seat-v1`
- `maps` lists every roster name with `mountpoint`, integer `generation`,
  `source`, and boolean `active`
- `holds` lists every hold window as `{key, until_epoch}`
- `seating_ok` is true only when every roster map's active bit and source
  agree with durable authority

Activity rules
--------------

1. Durable floors live under `/var/lib/autofs/floors/<name>.floor` as a single
   integer. A tip generation at or above that floor may be active (equality
   inclusive). Live sheets under `/etc/autofs/floors/` are not the durable
   authority.

2. Hold windows under `/var/lib/autofs/holds/<key>.hold` carry `until_epoch`.
   Compare against `/var/lib/autofs/state/clock.epoch`. An expired window keeps
   the related map inactive. Holds still appear in the `holds` array.

3. Drop-ins under `/etc/auto.master.d/` fold in lexical filename order; later
   files override earlier keys. An `abort=<name>` value from a later drop-in
   forces that map inactive even when generation and hold would allow it.

4. Abort-window residue under `/var/lib/autofs/ops/abort.d/` rematerializes
   into live drop-ins on every seating pass unless
   `/var/lib/autofs/state/cutover.ok` exists as plain `key=value` lines with
   exactly `gen=<target>` (matching `/var/lib/autofs/state/gen.target`) and
   `mode=seal`. A matching receipt skips rematerialize; it does **not** mean
   delete the live drop-in. `/etc/auto.master.d/90-local.conf` must remain
   present and carry site-standard tokens from `/app/config/site_standard.conf`
   (`tip_policy`, `bind_order`, `abort`). The abort package itself stays
   forensic with its original synonym tokens.

5. Each map `source` must be `/var/lib/autofs/maps/<name>.map` (durable copy),
   not a live tip path under `/etc/autofs/`.

6. Ops journal under `/var/lib/autofs/ops/journal.jsonl` records cutover rows.
   The sealed cutover for `gen.target` is authoritative; after apply,
   `gen.live` equals `gen.target`.

7. Two sequential seating runs must leave byte-identical
   `/output/autofs-seat.json`.
