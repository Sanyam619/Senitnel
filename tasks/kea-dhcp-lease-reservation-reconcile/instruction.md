Live Kea DHCP4 seating under `/etc/kea/`, `/etc/kea/kea-dhcp4.d/`, `/var/lib/kea/`, and `/var/run/kea/` drifted from durable pool and lease authority. Surface `/usr/local/bin/keahealth` may look fine while deep seating has drifted. Frozen fixtures under `/app/data/kea/` are integrity-pinned; do not rewrite them. Operator seating starts at `/app/ops/run_dhcp_seat.sh`.

Produce `/output/dhcp-seat.json`. Acceptance rules for durable pool preference, conf.d fold, generation floors, sealed memfile continuity, reservation honor, conflict ledgers, and cutover receipts live under `/app/docs/`.

Abort-window residue under `/var/lib/kea/ops/abort.d/` rematerializes into live kea-dhcp4.d on every seating pass unless a matching durable receipt exists at `/var/lib/kea/state/cutover.ok`. A matching receipt skips rematerialize; it does not mean delete the live drop-in. Live `/etc/kea/kea-dhcp4.d/90-local.conf` must remain on disk with site-standard tokens; the abort package stays forensic. Two seating runs must leave byte-identical `/output/dhcp-seat.json`.

Ledger vocabulary: schema_tag, subnets, id, pool, generation, reservations, hw, ip, subnet, honored, conflicts, reason, seat_ok. Reservation and conflict row order is free. Each subnet generation is the sealed journal tip for that subnet id.
