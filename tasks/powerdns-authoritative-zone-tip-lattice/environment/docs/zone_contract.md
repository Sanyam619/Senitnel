Zone Seating Contract
=====================

Graded seating produces `/output/pdns-seat.json`:

- `schema_tag` must be the literal string `pdns-seat-v1`
- `zones` lists every roster zone with integer `serial`, `backend`
  (string), integer `generation`, and boolean `published`
- `records` lists every record of the applied zone tip with `zone`,
  `name`, `type`, `content` (the live sheet content), and boolean
  `honored`
- `seat_ok` is true only when every roster zone agrees with durable
  authority (tip serial and generation, backing store selection,
  fold abort set, record honor), live `90-local.conf` carries
  site-standard tokens, the preference mode is `durable` or
  `authority`, tip bind acceptance matches `gen.target`, and the
  selected backing store is not retired. Agreement means each zone
  and record carries its durable verdict — a correct seat reports
  `seat_ok` true even though below-floor or aborted zones carry
  `published=false` and held records carry `honored=false`.
  Universal publication is not required and is not correct for this
  desk.

Preference
----------

`/var/lib/powerdns/ops/prefer.toml` is a read-only operator input. The
seating pipeline reads and respects it; it does not force the mode.
`durable` or `authority` is required for a durable seat. Modes `live`
and `surface` degrade the seat and keep surface tip, zone-sheet, and
serial materials under `/var/lib/powerdns/surface/` in play across
rematerialize. `/var/lib/powerdns/ops/tip_bind.accept` is a
pipeline-written receipt: seating rewrites it from `gen.target` on
every pass, so a durable seat carries `gen=<gen.target>` without a
static hand edit of that file.

Outcomes
--------

- Durable zone tips live in `/var/lib/powerdns/ops/zone_journal.jsonl`.
  The authoritative batch is the latest `sealed` and `complete` batch
  whose `gen` matches `/var/lib/powerdns/state/gen.target`. Incomplete
  later batches are not selected, and an earlier revision of the target
  generation is superseded by a later one. After apply, `gen.live`
  equals `gen.target`, and each zone tip is recorded as
  `/var/lib/powerdns/state/tip_<zone>.serial`, `tip_<zone>.gen`, and
  `tip_<zone>.records`.
- The selected backing store is the highest-epoch binding in
  `/var/lib/powerdns/ops/store_registry.jsonl` that does not appear in
  the retirement ledger `/var/lib/powerdns/ops/retired_stores.jsonl`.
  The selection is recorded at `/var/lib/powerdns/state/store.sel`, and
  every live `<zone>.store` sheet must carry it. The `launch=` line in
  live `pdns.conf` and the leftover single-file store under
  `/var/lib/powerdns/` are not seating authority.
- Durable floors live under `/var/lib/powerdns/floors/<zone>.floor`. A
  tip generation at or above that floor may be in service (equality
  inclusive). Live sheets under `/etc/powerdns/floors/` are not
  authority.
- pdns.d drop-ins fold `opt.` keys last-writer-wins and `abort-zone`
  names as a union. Residual abort policy does not survive a successful
  cutover into live `90-local.conf`. The base and lab drop-ins
  (`10-core.conf`, `40-lab.conf`) are desk policy and stay as shipped;
  `90-local.conf` is the only cutover surface.
- Abort residue under `/var/lib/powerdns/ops/abort.d/` rematerializes
  into live pdns.d unless `/var/lib/powerdns/state/cutover.ok` already
  matches as plain `key=value` with `gen=<target>` and `mode=seal`. A
  matching receipt skips rematerialize; it does not mean delete the
  live drop-in. Within one successful seating pass those steps are
  ordered: abort rematerialize may run first when the receipt does not
  match, then seating installs site-standard tokens from
  `/app/config/site_standard.conf` into live `90-local.conf` so the
  live drop-in does not remain on abort residue (`prefer_abort`), and
  seating emits `/var/lib/powerdns/state/cutover.ok` with
  `gen=<gen.target>` and `mode=seal`. Live `90-local.conf` must remain
  present. The abort package itself stays forensic.
- A zone is `published=true` only when its live serial sheet equals the
  applied tip serial, the tip generation is at or above the durable
  floor, its live store sheet equals the selected backing store, and
  the zone is not in the folded abort set. Live serial and store
  sheets are written for every roster zone whether or not it publishes.
- Record holds in `/var/lib/powerdns/ops/holds.jsonl` pin a record's
  live content: when a hold targets a record, the live sheet must carry
  the hold content instead of the tip content. `honored` is true only
  when the live content equals the sealed tip content, so held records
  report `honored=false` on a correct seat. Any other divergence from
  the tip (or from a hold) is a seating fault.
- Each live `<zone>.rec` sheet begins with the durable apex line
  `@ NS <ns>` where `<ns>` comes from
  `/var/lib/powerdns/zones/<zone>.ns`. Apex lines are not tip records
  and do not appear in the `records` ledger.
