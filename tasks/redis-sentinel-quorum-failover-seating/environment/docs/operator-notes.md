Operator notes
==============

Surface health prints MASTER-OK whenever monitor drop-ins are present. That
probe does not consult the failover journal tip, durable floors, prefer
plane, or replica attach state.

Frozen master descriptors under `/app/data/redis/masters/` are packaging
pins. Sealed copies under `/var/lib/redis/masters/` must keep matching them
after seating.

Operator seating starts at `/app/ops/run_sentinel_seat.sh`. Prefer the durable
ops plane before expecting live sentinel monitor lines to survive a second
pass.
