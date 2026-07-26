Layout
======

- `/etc/openvpn/server/server.conf` — base server sheet
- `/etc/openvpn/server/conf.d/` — pool-policy and abort drop-ins (lexical fold)
- `/etc/openvpn/ccd/` — live per-client CCD sheets (`<cn>` files with iroute lines)
- `/etc/openvpn/server/floors/` — live generation sheets (not durable authority)
- `/etc/openvpn/server/roster.list` — client roster order
- `/var/lib/openvpn/ops/prefer.jsonl` — durable prefer tip batches
- `/var/lib/openvpn/ops/prefer.toml` — preference mode (`live`/`surface` vs
  `durable`/`authority`)
- `/var/lib/openvpn/ops/tip_bind.accept` — tip bind acceptance receipt
- `/var/lib/openvpn/ops/clients.jsonl` — sealed client admit/revoke journal
- `/var/lib/openvpn/ops/pools.toml` — durable pool roster and CIDRs
- `/var/lib/openvpn/ops/abort.d/` — abort-window residue package
- `/var/lib/openvpn/surface/` — surface tip and CCD materials used when
  preference is not durable
- `/var/lib/openvpn/floors/` — durable generation floors
- `/var/lib/openvpn/state/` — gen.target, gen.live, tip_*.gen, tip_*.iroute,
  cutover.ok (emitted seating receipt: gen + mode=seal), pool and push flags
- `/app/data/ovpn/` — frozen client fixtures
- `/app/config/site_standard.conf` — site-standard live drop-in tokens
- `/app/ops/run_ovpn_seat.sh` — seating entrypoint
