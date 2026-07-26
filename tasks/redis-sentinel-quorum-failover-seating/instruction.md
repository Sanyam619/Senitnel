Bring Redis Sentinel high availability back into agreement on the live host
configs and publish a correct seating report.

Live Redis materials under `/etc/redis/` and `/etc/redis/sentinel.d/` drifted
from durable ops state under `/var/lib/redis/ops/`. Surface
`/usr/local/bin/redishhealth` may print MASTER-OK while deep seating is wrong,
and monitor edits made without settling the desk are gone again on the next
pass.

Produce `/output/sentinel-seat.json` by running `/app/ops/run_sentinel_seat.sh`.
It carries schema_tag sentinel-seat-v1, one masters row per roster master
(name, addr, generation, authoritative), the replicas rows (master, addr, lag,
attached), and seat_ok. Acceptance rules — journal tip agreement, generation
floors, quorum under the prefer-selected policy, replica attach against
superseded masters, the drop-in policy fold, and the receipt the state plane
must carry — live under `/app/docs/`. Frozen fixtures under `/app/data/redis/`
must stay unchanged, and sealed copies under `/var/lib/redis/masters/` must
keep matching them. Grading clears `/output` and re-runs the desk twice; the
two reports must be byte-identical. Hand-authored JSON fails.

Ledger vocabulary: schema_tag, masters, name, addr, generation, authoritative,
replicas, master, lag, attached, seat_ok.
