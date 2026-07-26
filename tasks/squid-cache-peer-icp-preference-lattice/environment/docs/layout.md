Layout
======

- `/etc/squid/squid.conf` — base proxy sheet
- `/etc/squid/conf.d/` — ACL and peer-policy drop-ins (lexical fold)
- `/etc/squid/peers.d/` — live peer sheets (`<name>.peer`)
- `/etc/squid/floors/` — live generation sheets (not durable authority)
- `/etc/squid/roster.list` — peer roster order
- `/var/lib/squid/ops/prefer.jsonl` — durable prefer tip batches
- `/var/lib/squid/ops/prefer.toml` — preference mode (`live`/`surface` vs
  `durable`/`authority`)
- `/var/lib/squid/ops/tip_bind.accept` — tip bind acceptance receipt
- `/var/lib/squid/ops/peers.jsonl` — sealed peer admit/revoke journal
- `/var/lib/squid/ops/abort.d/` — abort-window residue package
- `/var/lib/squid/surface/` — surface tip and peer-sheet materials used
  when preference is not durable
- `/var/lib/squid/floors/` — durable generation floors
- `/var/lib/squid/peers/` — durable host addresses from fixtures
- `/var/lib/squid/state/` — gen.target, gen.live, tip_*.gen, tip_*.type,
  tip_*.weight, cutover.ok (emitted seating receipt: gen + mode=seal),
  flags
- `/app/data/squid/` — frozen peer fixtures
- `/app/config/site_standard.conf` — site-standard live drop-in tokens
- `/app/ops/run_squid_seat.sh` — seating entrypoint
