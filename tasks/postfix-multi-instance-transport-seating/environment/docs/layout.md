Layout
======

- `/etc/postfix/main.cf` — shared base sheet
- `/etc/postfix/master.d/` — master drop-ins (lexical fold)
- `/etc/postfix/maps/nexthop.live` — live decoy nexthop map
- `/etc/postfix/floors/` — live generation sheets (not durable authority)
- `/etc/postfix/roster.list` — instance roster order
- `/etc/postfix-<name>/main.cf` — per-instance sheet (`queue_directory`,
  `transport_maps`); e.g. `/etc/postfix-mesa/main.cf`
- `/var/lib/postfix/ops/prefer.jsonl` — durable prefer tip batches
- `/var/lib/postfix/ops/prefer.toml` — preference mode (`live`/`surface` vs
  `durable`/`authority`)
- `/var/lib/postfix/ops/tip_bind.accept` — tip bind acceptance receipt
- `/var/lib/postfix/ops/instances.jsonl` — sealed instance admit/revoke journal
- `/var/lib/postfix/ops/maps/nexthop.prefer` — working prefer nexthop map
  (may be rematerialized from surface when preference is live/surface)
- `/var/lib/postfix/ops/maps/nexthop.durable` — durable authority nexthop
  map copy (not overwritten by surface rematerialize; source for durable
  restore into `nexthop.prefer`)
- `/var/lib/postfix/ops/abort.d/` — abort-window residue package (master
  drop-in + transport fragment)
- `/var/lib/postfix/surface/` — surface tip and map materials used when
  preference is not durable
- `/var/lib/postfix/floors/` — durable generation floors
- `/var/lib/postfix/state/` — gen.target, gen.live, tip_*.gen, tip_*.queue,
  cutover.ok (emitted seating receipt: gen + mode=seal), flags
- `/app/data/postfix/` — frozen instance fixtures
- `/app/packaging/instances.sha256` — sha256 inventory of those fixtures
- `/app/config/site_standard.conf` — site-standard live master.d tokens
- `/app/ops/run_postfix_seat.sh` — seating entrypoint
- Surface/live decoy spool paths (not durable tip authority) include
  `/var/spool/postfix-mesa-decoy` and superseded batch residue such as
  `/var/spool/postfix-mesa-wrong`; durable mesa tip is
  `/var/spool/postfix-mesa`.
