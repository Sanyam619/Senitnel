Seating Contract
================

Graded seating produces `/output/lvmcache-seat.json`:

- `schema_tag` must be the literal string `lvmcache-seat-v1`
- `volumes` lists every roster entry with `name`, `vg`, `mode`,
  `cachepool`, integer `generation`, and boolean `attached`
- `holds` lists every maintenance window as `{lv, until_epoch}`
- `seat_ok` is true only when every roster volume agrees with the durable
  authority and the state plane carries a matching receipt

Activity rules
--------------

1. Durable generation floors live under `/var/lib/lvm/floors/<name>.floor`
   as a single integer. A tip generation at or above that floor may attach
   (equality inclusive). The live sheets under `/etc/lvm/floors/` are kept
   for the surface probe and are not the durable authority.

2. The mode journal under `/var/lib/lvm/ops/journal.jsonl` records desk
   windows. The authoritative row is the cutover row whose generation
   equals `/var/lib/lvm/state/gen.target` and whose mode is sealed; it
   carries the per-volume tip generation and the per-volume cache mode.
   Older sealed windows and later provisional re-opens are history, not
   authority. After apply, `/var/lib/lvm/state/gen.live` equals
   `gen.target`.

3. Cachepool identity is fixed by the sealed map
   `/var/lib/lvm/ops/pool.map`, a copy of the frozen fixture
   `/app/data/lvm/pool.map`. The ledger reports that sealed identity. A
   live sheet under `/etc/lvm/cache.d/` whose `pool_uuid` or `cache_mode`
   disagrees with the sealed identity and the durable tip mode leaves the
   volume unattached.

4. Maintenance windows under `/var/lib/lvm/holds/<lv>.hold` carry
   `until_epoch` and compare against `/var/lib/lvm/state/clock.epoch`. A
   window that is still open (`until_epoch` greater than the clock) keeps
   the related volume unattached. An expired window has no effect on
   attachment. Every window still appears in the `holds` array.

5. Drop-ins under `/etc/lvm/lvm.conf.d/` fold in lexical filename order;
   later files override earlier keys. An `abort=<name>` value in the
   folded result forces that volume unattached even when generation, mode
   and window would allow it.

6. `/var/lib/lvm/ops/prefer.toml` selects the material plane for the live
   cache sheets. On the surface plane the desk refreshes every live sheet
   from the pre-cutover working sheet `/var/lib/lvm/ops/surface.modes` on
   each pass, rematerializes the abort package into the live drop-ins, and
   drops the apply receipt. The durable plane additionally requires
   `/var/lib/lvm/ops/state/apply.ok` as plain `key=value` lines carrying
   exactly `gen=<target>` (matching `gen.target`) and `mode=seal`. With the
   durable plane and a matching receipt the desk refreshes the live sheets
   from the sealed durable image instead and leaves the live drop-ins
   alone.

7. A matching receipt is not an instruction to delete the live drop-in.
   `/etc/lvm/lvm.conf.d/90-local.conf` must remain present and carry the
   site-standard tokens from `/app/config/site_standard.conf`
   (`tip_policy`, `bind_order`, `abort`). The abort package under
   `/var/lib/lvm/ops/abort.d/` stays forensic with its original synonym
   tokens.

8. Two sequential seating passes must leave `/output/lvmcache-seat.json`
   byte-identical.
