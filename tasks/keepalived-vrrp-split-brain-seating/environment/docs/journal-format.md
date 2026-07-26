Journal rows and eligibility
============================

Preference batches live in `/var/lib/keepalived/ops/prefer.jsonl` as JSON
objects with `kind=batch`, integer `gen`, booleans `sealed` and `complete`,
and a `rows` array of `{id, tip, rank}` objects. Only a sealed and complete
batch is authoritative; among those, the highest `gen` wins. Incomplete later
batches are not selected. The `tip` is the peer generation; the `rank` breaks
ties between equal effective priorities on the same VRID, and the higher rank
wins.

Transition rows live in `/var/lib/keepalived/ops/transitions.jsonl`:

- `kind=move` carries `eid`, `vrid`, `epoch`, `from`, `to`
- `kind=retract` carries `eid` and `epoch`

A retraction cancels the move with the matching `eid` only. An unretracted
move whose `from` is MASTER vetoes MASTER for that VRID.

Hold files under `/var/lib/keepalived/ops/holds/<id>.hold` carry `until=<epoch>`.
Compare against `/var/lib/keepalived/ops/state/clock.epoch`. A hold is active
when `until` is strictly greater than the clock.

Floor files under `/var/lib/keepalived/ops/floors/<id>.floor` are a single
integer. Interface generation files under
`/var/lib/keepalived/ops/netif/<id>.gen` are a single integer. A peer may be
eligible only when its tip and its interface generation are both at or above
the floor, and its hold is inactive.

Scenario: peer_e may carry a high folded priority and an inactive hold at
`until == clock`, yet still stay BACKUP when its tip sits below the floor.
Scenario: peer_b may outrank peer_a on folded priority yet stay BACKUP while
its hold remains active. Scenario: two peers tie on effective priority for a
VRID and the one with the higher durable rank seats MASTER. Scenario: two
MASTER peers on VRID 51 and VRID 52 at once is normal; two MASTER peers on the
same VRID is split-brain.
