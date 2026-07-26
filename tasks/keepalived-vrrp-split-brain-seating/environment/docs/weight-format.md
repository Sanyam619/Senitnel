Weight records
==============

Drop-ins under `/etc/keepalived/conf.d/` are read in lexical filename order.
Each non-comment line is one of:

- `peer_x.prio=<integer>` — assign absolute priority for that peer
- `replace peer_x.prio=<integer>` — scoped absolute assign (same effect as assign)
- `delta peer_x.prio=<integer>` — add the signed integer to the current folded value

Later records override earlier absolute assigns for the same peer. Deltas apply
to the running folded value at the moment they appear. Non-priority keys such as
`bind_order` or `tip_policy` do not enter the priority table.

Track-script sheets under `/var/lib/keepalived/ops/track/<id>.wt` carry
`delta=<integer>`. The matching `/var/lib/keepalived/ops/track/<id>.status` probe
must read `UP` for that delta to apply after the conf.d fold. A `DOWN` (or
missing) probe leaves the folded priority unchanged for that peer.

Effective priorities are integers after fold and UP-only track application.
