# Access-state and generation bands

An ALUA target group advertises one of several access states. Only groups in
the **active/optimized** (AO) state carry the preferred I/O path. A group in
**active/non-optimized** (ANO) state still reports as up and will pass a naive
path count, but it is not the optimized target and must never be seated as the
active path. **standby** and **unavailable** groups are never eligible.

Each path also carries a monotonically increasing generation stamp. A path is
only eligible when its generation is at or above the durable floor recorded as
`min_generation` in the fabric authority. A stale AO path whose generation is
below the floor is rejected even when its priority is high.

When more than one eligible AO path remains for a map, the active path is the
one with the highest priority; ties break toward the lexically smallest path
device name.
