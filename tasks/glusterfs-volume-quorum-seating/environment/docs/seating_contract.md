Seating Contract
================

Graded seating produces `/output/gluster-seat.json`:

- `schema_tag` must be the literal string `gluster-seat-v1`
- `volumes` lists every roster entry with `name`, `bricks` (array of
  absolute brick paths), integer `quorum`, integer `generation`, and
  boolean `started`
- `heals` lists every roster volume as `{volume, pending}` where `pending`
  is the count of open held bricks that belong to that volume's durable
  brick set
- `seat_ok` is true only when every roster volume agrees with the durable
  authority and the state plane carries a matching receipt

Activity rules
--------------

1. Durable generation floors live under
   `/var/lib/glusterd/floors/<name>.floor` as a single integer. A tip
   generation at or above that floor may start (equality inclusive). The
   live sheets under `/etc/glusterfs/floors/` are kept for the surface
   probe and are not the durable authority.

2. The brick journal under `/var/lib/glusterd/ops/brick_journal.jsonl`
   records desk windows. The authoritative row is the cutover row whose
   generation equals `/var/lib/glusterd/state/gen.target` and whose mode
   is sealed; it carries the per-volume tip generation, the durable brick
   path set, and the per-volume quorum integer. Older sealed windows and
   later provisional re-opens are history, not authority. After apply,
   `/var/lib/glusterd/state/gen.live` equals `gen.target`.

3. A volume may start only when the live brick sheet under
   `/etc/glusterfs/bricks.d/<name>.bricks` lists exactly the durable
   journal brick set (order-insensitive), the tip generation clears the
   durable floor, quorum is satisfied under the prefer-selected policy,
   and no held brick from that durable set remains in the started brick
   list. The durable quorum policy uses the sealed per-volume quorum
   integer: at least that many durable bricks must be present and not
   held. The surface probe does not enforce these rules.

4. Holds under `/var/lib/glusterd/holds/<brick-id>.hold` name a brick path
   and an `until_epoch`, compared against
   `/var/lib/glusterd/state/clock.epoch`. An open hold
   (`until_epoch` greater than the clock) blocks every volume whose
   durable set contains that brick and increments that volume's heal
   `pending` by one. An expired hold has no effect on starting. Every
   roster volume still appears in `heals`.

5. Drop-ins under `/etc/glusterfs/glusterd.d/` fold in lexical filename
   order; later files override earlier keys. An `abort=<name>` value in
   the folded result forces that volume not started even when generation,
   bricks, quorum and holds would allow it.

6. `/var/lib/glusterd/ops/prefer.toml` selects the material plane for the
   live brick sheets. On the surface plane the desk refreshes every live
   sheet from the pre-cutover working sheet
   `/var/lib/glusterd/ops/surface.bricks` on each pass, rematerializes the
   abort package into the live drop-ins, and drops the apply receipt. The
   durable plane additionally requires
   `/var/lib/glusterd/ops/state/apply.ok` as plain `key=value` lines
   carrying exactly `gen=<target>` (matching `gen.target`) and
   `mode=seal`. With the durable plane and a matching receipt the desk
   refreshes the live sheets from the sealed durable brick sets instead
   and leaves the live drop-ins alone.

7. A matching receipt is not an instruction to delete the live drop-in.
   `/etc/glusterfs/glusterd.d/90-local.conf` must remain present and carry
   the site-standard tokens from `/app/config/site_standard.conf`
   (`tip_policy`, `bind_order`, `abort`). The abort package under
   `/var/lib/glusterd/ops/abort.d/` stays forensic with its original
   synonym tokens.

8. Two sequential seating passes must leave `/output/gluster-seat.json`
   byte-identical. Hand-written stand-ins that skip the seating path fail
   re-entry.
