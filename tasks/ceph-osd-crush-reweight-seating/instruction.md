Live object-storage placement seating under `/etc/ceph/` and `/var/lib/ceph/ops/` was captured mid-cutover and drifted from the durable placement authority. `/usr/local/bin/cephhealth` keeps printing `HEALTH_OK`, but deep seating is wrong, and edits made without settling the desk do not stick between passes.

Bring the desk to a correct, durable end-state and produce `/output/crush-seat.json` via `/app/ops/run_crush_seat.sh`. Acceptance rules — device standing against the durable authority and the sealed out-journal, maintenance hold windows, group degradation computed from the seated spread, and the receipt the state plane must carry — live under `/app/docs/`.

Frozen fixtures under `/app/data/` are integrity-pinned; do not rewrite them, and the sealed copies under `/var/lib/ceph/ops/` must continue to match them. Grading clears `/output` and re-runs the desk twice; the two reports must be byte-identical.

Ledger vocabulary: schema_tag, osds, id, host, weight, in, up, generation, pools, name, size, pg_num, degraded, seat_ok.
