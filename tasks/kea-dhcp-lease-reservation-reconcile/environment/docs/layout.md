Layout
======

- `/etc/kea/kea-dhcp4.conf` — base include stub
- `/etc/kea/kea-dhcp4.d/` — lexical drop-ins
- `/etc/kea/floors/` — live floor sheets (operator scratch)
- `/etc/kea/pools/` — live decoy pools (`<id>.pool`)
- `/var/lib/kea/floors/` — durable floors
- `/var/lib/kea/pools/` — durable subnet pools
- `/var/lib/kea/ops/prefer.toml` — durable vs live pool preference
- `/var/lib/kea/ops/memfile.csv` — sealed lease memfile
- `/var/lib/kea/ops/abort.d/` — abort-window package
- `/var/lib/kea/ops/journal.jsonl` — tip journal
- `/var/lib/kea/state/` — gen.target, gen.live, cutover.ok, tip_*.gen
- `/var/run/kea/` — runtime seating scratch
- `/app/data/kea/` — frozen subnet fixture definitions
- `/app/data/seed/kea-dhcp4.d/10-core.conf` — seed core drop-in
- `/app/data/seed/kea-dhcp4.d/40-lab.conf` — seed lab drop-in
- `/app/packaging/kea.sha256` — operator packaging pin (verifier uses its own ledger)
- `/app/ops/run_dhcp_seat.sh` — seating entrypoint
