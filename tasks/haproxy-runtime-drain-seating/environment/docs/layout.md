Layout
======

- `/etc/haproxy/haproxy.cfg` — base include stub
- `/etc/haproxy/conf.d/` — lexical drop-ins
- `/etc/haproxy/floors/` — live floor sheets (operator scratch)
- `/var/lib/haproxy/floors/` — durable floors
- `/var/lib/haproxy/backends/` — durable server addresses
- `/var/lib/haproxy/leases/` — drain leases
- `/var/lib/haproxy/ops/abort.d/` — abort-window package
- `/var/lib/haproxy/ops/journal.jsonl` — tip journal
- `/var/lib/haproxy/state/` — clock, gen.target, gen.live, cutover.ok, tip_*.gen,
  drain flags, and `effective.conf` (folded conf.d result used for seating)
- `/var/run/haproxy/runtime.map` — runtime socket apply image
- `/var/run/haproxy/socket.applied` — apply marker (`1` when map was written)
- `/app/data/backends/` — frozen fixture definitions
- `/app/ops/run_proxy_seat.sh` — seating entrypoint
