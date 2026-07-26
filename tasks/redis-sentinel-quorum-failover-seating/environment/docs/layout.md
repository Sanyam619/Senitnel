Redis Sentinel seating layout
=============================

Live plane
----------
- `/etc/redis/roster.list` — master names on the desk
- `/etc/redis/replica.list` — replica rows (master, replica addr, reported master, lag)
- `/etc/redis/sentinel.d/` — lexical drop-in fold into `/etc/redis/effective.conf`
- `/etc/redis/monitors.d/<name>.conf` — live sentinel monitor lines per master
- `/etc/redis/floors/<name>.floor` — surface generation floors (probe only)

Durable plane
-------------
- `/var/lib/redis/ops/prefer.toml` — material plane (`surface` or `durable`)
- `/var/lib/redis/ops/failover_journal.jsonl` — failover windows
- `/var/lib/redis/ops/surface.monitors` / `surface.quorum` — pre-cutover decoy sheets
- `/var/lib/redis/ops/abort.d/` — abort package (forensic after settle)
- `/var/lib/redis/ops/state/apply.ok` — apply receipt (`key=value`)
- `/var/lib/redis/state/gen.target`, `gen.live`, `clock.epoch`
- `/var/lib/redis/floors/<name>.floor` — durable generation floors
- `/var/lib/redis/masters/` — sealed master descriptors (must match frozen fixtures)

Entrypoints
-----------
- `/app/ops/run_sentinel_seat.sh` — live seating pass
- `/usr/local/bin/redishhealth` — surface MASTER-OK probe
