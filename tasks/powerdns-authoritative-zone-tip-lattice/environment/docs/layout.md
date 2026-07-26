Layout
======

- `/etc/powerdns/pdns.conf` — base server sheet (launch line is not
  seating authority)
- `/etc/powerdns/pdns.d/` — option and policy drop-ins (lexical fold)
- `/etc/powerdns/zones.d/` — live zone sheets: `<zone>.rec` record
  sheets and `<zone>.store` backing-store sheets
- `/etc/powerdns/serials/` — live serial sheets (`<zone>.serial`)
- `/etc/powerdns/floors/` — live generation sheets (not durable
  authority)
- `/etc/powerdns/zone.roster` — zone roster order
- `/var/lib/powerdns/ops/zone_journal.jsonl` — durable zone tip batches
- `/var/lib/powerdns/ops/prefer.toml` — operator preference input
  (`live`/`surface` vs `durable`/`authority`); seating reads it and
  does not rewrite it
- `/var/lib/powerdns/ops/tip_bind.accept` — tip bind acceptance receipt
  rewritten by seating from `gen.target` each pass
- `/var/lib/powerdns/ops/store_registry.jsonl` — backing store bindings
  by epoch
- `/var/lib/powerdns/ops/retired_stores.jsonl` — store retirement ledger
- `/var/lib/powerdns/ops/holds.jsonl` — record hold ledger
- `/var/lib/powerdns/ops/abort.d/` — abort-window residue package
- `/var/lib/powerdns/surface/` — surface tip, zone-sheet, and serial
  materials used when preference is not durable
- `/var/lib/powerdns/floors/` — durable generation floors
- `/var/lib/powerdns/zones/` — durable apex data (`<zone>.ns`) from
  frozen fixtures
- `/var/lib/powerdns/state/` — gen.target, gen.live, tip_<zone>.serial,
  tip_<zone>.gen, tip_<zone>.records, store.sel, publish.set, honor.set,
  abort.set, opts.fold, cutover.ok (emitted seating receipt: gen +
  mode=seal), flags
- `/var/lib/powerdns/pdns.sqlite3` — leftover single-file store
- `/app/data/pdns/` — frozen zone fixtures
- `/app/config/site_standard.conf` — site-standard live drop-in tokens
- `/app/ops/run_pdns_seat.sh` — seating entrypoint
