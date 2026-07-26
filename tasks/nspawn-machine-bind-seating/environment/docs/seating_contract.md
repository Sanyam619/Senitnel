Seating Contract
================

Graded seating produces `/output/nspawn-seat.json`:

- `schema_tag` must be the literal string `nspawn-seat-v1`
- `machines` lists every roster name with `root`, `bind` (array of strings),
  integer `generation`, and boolean `active`
- `ports` lists every durable port row as `{machine, host, container}`
- `seat_ok` is true only when every roster machine's active bit, root, and
  bind list agree with durable authority

Activity rules
--------------

1. Durable image tip for each machine is
   `/var/lib/machines/images/<name>/root`. Live shadow roots under
   `/var/lib/machines/live/<name>/root` are not authoritative. An active
   machine must list the durable tip as `root`. A seating pass must also
   rewrite the live unit `/etc/systemd/nspawn/<name>.nspawn` so its
   `Directory=` line is exactly that durable tip for every roster
   machine (one `Directory=` line, not a live-shadow path).

2. Durable floors live under `/var/lib/machines/floors/<name>.floor` as a
   single integer. A tip generation at or above that floor may be active
   (equality inclusive). Live sheets under `/etc/systemd/nspawn/floors/`
   are not the durable authority.

3. Each machine's `Bind=` paths under `/etc/systemd/nspawn/<name>.nspawn`
   must resolve to the same inode as the matching sealed object under
   `/var/lib/machines/volumes/<name>/`. Paths that only string-match a
   sealed object but are distinct inodes do not count as attached.

4. Drop-ins under `/etc/systemd/system/machines.target.wants/` fold in
   lexical filename order; later files override earlier keys. The folded
   policy is written to `/etc/systemd/nspawn/effective.conf`. After a
   seating pass that file must carry the site-standard `tip_policy`,
   `bind_order`, and `abort` tokens from `/app/config/site_standard.conf`.
   An `abort=<name>` value from a later drop-in forces that machine
   inactive even when tip, bind, and generation would allow it.

5. Abort-window residue under `/var/lib/machines/ops/abort.d/`
   rematerializes into live drop-ins on every seating pass unless
   `/var/lib/machines/state/cutover.ok` exists as plain `key=value` lines
   with exactly `gen=<target>` (matching
   `/var/lib/machines/state/gen.target`) and `mode=seal`. A matching
   receipt skips rematerialize; it does **not** mean delete the live
   drop-in. `/etc/systemd/system/machines.target.wants/90-local.conf`
   must remain present and carry site-standard tokens from
   `/app/config/site_standard.conf` (`tip_policy`, `bind_order`,
   `abort`). The abort package itself stays forensic with its original
   synonym tokens.

6. Ports come from durable rows under `/var/lib/machines/ops/ports.toml`
   (not the live sheet under `/etc/systemd/nspawn/ports.toml`).

7. Ops journal under `/var/lib/machines/ops/journal.jsonl` records cutover
   rows. The sealed cutover for `gen.target` is authoritative; after
   apply, `gen.live` equals `gen.target`.

8. Two sequential seating runs must leave byte-identical
   `/output/nspawn-seat.json`.
