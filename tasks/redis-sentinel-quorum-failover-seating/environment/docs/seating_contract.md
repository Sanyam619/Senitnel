Seating Contract
================

Graded seating produces `/output/sentinel-seat.json`:

- `schema_tag` must be the literal string `sentinel-seat-v1`
- `masters` lists every roster master with `name` (string), `addr` (string),
  integer `generation`, and boolean `authoritative`
- `replicas` lists every replica row with `master` (string), `addr` (string),
  integer `lag`, and boolean `attached`
- `seat_ok` is true only when every roster master agrees with the durable
  authority and the state plane carries a matching receipt

Activity rules
--------------

1. Durable generation floors live under
   `/var/lib/redis/floors/<name>.floor` as a single integer. A tip
   generation at or above that floor may be authoritative (equality
   inclusive). Live floors under `/etc/redis/floors/` are for the surface
   probe and are not durable authority.

2. The failover journal under
   `/var/lib/redis/ops/failover_journal.jsonl` records desk windows. The
   authoritative row is the cutover row whose generation equals
   `/var/lib/redis/state/gen.target` and whose mode is sealed; it carries
   per-master tip `addr` + `generation`, the durable quorum integer, and
   the `sentinels_online` list used to evaluate that quorum. Older sealed
   windows and later provisional re-opens are history, not authority. After
   apply, `/var/lib/redis/state/gen.live` equals `gen.target`.

3. A master is `authoritative` only when its published `addr` equals the
   durable journal tip addr for that name, the tip generation clears the
   durable floor, quorum is satisfied under the prefer-selected policy, and
   the folded effective policy does not abort that master. The durable
   quorum policy requires at least the sealed quorum integer of online
   sentinels from the tip row. The surface probe does not enforce these
   rules.

4. A replica row is `attached` only when its reported master address equals
   the durable tip addr for that replica's master name. Replicas that still
   report a superseded master address have `attached=false`. Lag comes from
   the replica sheet. Every replica.list row appears in `replicas`.

5. Drop-ins under `/etc/redis/sentinel.d/` fold in lexical filename order;
   later files override earlier keys. An `abort=<name>` value in the folded
   result forces that master not authoritative even when generation, addr,
   and quorum would allow it.

6. `/var/lib/redis/ops/prefer.toml` selects the material plane for live
   monitor lines. On the surface plane the desk refreshes every live
   monitor from the pre-cutover working sheet
   `/var/lib/redis/ops/surface.monitors` on each pass, rematerializes the
   abort package into the live drop-ins, applies the surface quorum sheet,
   and drops the apply receipt. The durable plane additionally requires
   `/var/lib/redis/ops/state/apply.ok` as plain `key=value` lines carrying
   exactly `gen=<target>` (matching `gen.target`) and `mode=seal`. With the
   durable plane and a matching receipt the desk refreshes live monitors
   from the sealed durable tip addrs instead and leaves the live drop-ins
   alone.

7. A matching receipt is not an instruction to delete the live drop-in.
   `/etc/redis/sentinel.d/90-local.conf` must remain present and carry the
   site-standard tokens from `/app/config/site_standard.conf`
   (`tip_policy`, `bind_order`, `abort`). The abort package under
   `/var/lib/redis/ops/abort.d/` stays forensic with its original synonym
   tokens.

8. Two sequential seating passes must leave `/output/sentinel-seat.json`
   byte-identical. Hand-written stand-ins that skip the seating path fail
   re-entry.
