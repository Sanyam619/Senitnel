Live reverse-proxy seating under `/etc/haproxy/`, `/etc/haproxy/conf.d/`, `/var/lib/haproxy/`, and `/var/run/haproxy/` drifted from durable backend authority. Surface `/usr/local/bin/proxyhealth` may look fine while deep seating has drifted. Frozen fixtures under `/app/data/backends/` are integrity-pinned; do not rewrite them. Operator seating starts at `/app/ops/run_proxy_seat.sh`.

Produce `/output/proxy-seat.json`. Acceptance rules for conf.d fold (including the folded `effective.conf` under state), drain leases, generation reporting, runtime maps, and cutover receipts live under `/app/docs/`. Generation is the raw sealed-journal tip for each backend. A tip below its durable floor is still reported and does not by itself refuse seating.

Abort-window residue under `/var/lib/haproxy/ops/abort.d/` rematerializes into live conf.d on every seating pass unless a matching durable receipt exists at `/var/lib/haproxy/state/cutover.ok`. A matching receipt skips rematerialize; it does not mean delete the live drop-in. Live `/etc/haproxy/conf.d/90-local.cfg` must remain on disk with site-standard tokens; the abort package stays forensic. Two seating runs must leave byte-identical `/output/proxy-seat.json`.

Ledger vocabulary: schema_tag, backends, name, server, weight, drained, generation, socket_applied, seat_ok.
