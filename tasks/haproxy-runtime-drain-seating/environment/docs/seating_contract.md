Seating Contract
================

Graded seating produces `/output/proxy-seat.json`:

- `schema_tag` must be the literal string `proxy-seat-v1`
- `backends` lists every roster name with `server`, integer `weight`,
  boolean `drained`, and integer `generation`
- `socket_applied` is true only when `/var/run/haproxy/runtime.map`
  matches the folded conf.d weights and drain flags, and
  `/var/run/haproxy/socket.applied` is present with value `1`
- `seat_ok` is true only when every roster backend agrees with durable
  authority (defined below) and `socket_applied` is true

What "agrees with durable authority" means
-----------------------------------------

Agreement is field-level agreement on the ledger rows and live policy, not
an "in service" check. A backend agrees when all of the following hold:

1. `server` equals the durable address under
   `/var/lib/haproxy/backends/<name>.addr`
2. `weight` equals the folded site-standard weight (see fold rules)
3. `drained` matches the drain-lease rule against the desk clock
4. `generation` equals the raw sealed-journal tip for that name (see
   generation rule)
5. Live drop-in policy, cutover receipt, gen.live, and forensic abort.d
   match the cutover rules below
6. Runtime map lines match that backend's weight and drained bit

Floor vs seat_ok
----------------

Durable floors under `/var/lib/haproxy/floors/<name>.floor` are operator
policy for which tips are considered in-service (tip at or above the
floor, equality inclusive). That policy is **orthogonal** to ledger
`seat_ok`. A tip below its durable floor is still reported in
`backends[].generation`. Below-floor generation does **not** by itself
force `seat_ok` false and must not be treated as a seating refusal.
Live sheets under `/etc/haproxy/floors/` are not the durable authority.

Generation
----------

`backends[].generation` is the raw integer tip taken from the sealed
journal tip row for that name (materialized at
`/var/lib/haproxy/state/tip_<name>.gen` after journal apply). It is not
a floor residual, not a live-floor value, and not clamped to the floor.

Activity rules
--------------

1. Drain leases under `/var/lib/haproxy/leases/<name>.lease` carry
   `until_epoch`. Compare against `/var/lib/haproxy/state/clock.epoch`.
   An unexpired lease marks the backend `drained=true` and must keep the
   folded weight (do not zero weight to express drain). Expired leases do
   not drain.

2. Drop-ins under `/etc/haproxy/conf.d/` fold in lexical filename order into
   `/var/lib/haproxy/state/effective.conf`; later files override earlier
   `weight.<name>` and site tokens. An `abort=<name>` value from a later
   drop-in is residual policy noise that must not survive a successful
   cutover into live `90-local.cfg`.

3. Abort-window residue under `/var/lib/haproxy/ops/abort.d/` rematerializes
   into live conf.d on every seating pass unless
   `/var/lib/haproxy/state/cutover.ok` exists as plain `key=value` lines
   with exactly `gen=<target>` (matching `/var/lib/haproxy/state/gen.target`)
   and `mode=seal`. A matching receipt skips rematerialize; it does **not**
   mean delete the live drop-in. `/etc/haproxy/conf.d/90-local.cfg` must
   remain present and carry site-standard tokens from
   `/app/config/site_standard.conf` (`tip_policy`, `bind_order`, and
   `weight.<name>` lines). The abort package itself stays forensic with
   its original synonym tokens.

4. Runtime socket state is `/var/run/haproxy/runtime.map` with one line per
   backend: `<name> <weight> <drained_0_or_1>`. Files that look correct
   under `/etc/haproxy/` do not imply `socket_applied`.

5. Ops journal under `/var/lib/haproxy/ops/journal.jsonl` records cutover
   tip generations. The sealed cutover for `gen.target` is authoritative;
   after apply, `gen.live` equals `gen.target` and each `tip_<name>.gen`
   matches the journal tip for that name.
