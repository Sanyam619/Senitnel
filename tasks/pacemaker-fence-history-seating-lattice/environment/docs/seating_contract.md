Seating Contract
================

Graded seating produces `/output/crm-seat.json`:

- `schema_tag` must be the literal string `crm-seat-v1`
- `nodes` lists every roster node with boolean `online` and integer `generation`
- `resources` lists every roster resource with `id`, `node`, `role`, and integer
  `stickiness`
- `fences` lists sealed fence-history rows as `{target, epoch, status}`
- `seat_ok` is true only when nodes, resources, and fences agree with durable
  authority under `/var/lib/cluster/ops/` and `/var/lib/pacemaker/`

Placement rules
---------------

1. Durable prefer tips live in the sealed cutover row of
   `/var/lib/cluster/ops/prefer_journal.jsonl` for
   `/var/lib/cluster/ops/state/gen.target`. After apply, each node's published
   generation equals that tip and `gen.live` equals `gen.target`. Live sheets
   under `/etc/corosync/nodes/` are not the durable authority. A node is
   `online` only when its tip is at or above the durable floor under
   `/var/lib/pacemaker/floors/<name>.floor` (equality inclusive).

2. Drop-ins under `/etc/pacemaker/cib.d/` fold in lexical filename order; later
   files override earlier keys. The effective `default_stickiness` must match
   `/app/config/site_standard.conf`. Each resource's published `stickiness`
   must equal that effective value.

3. Sealed fence history is `/var/lib/cluster/ops/fence_journal.jsonl`. A target
   is unretracted when its latest status in epoch order is `fenced` (a later
   `retract` clears it). A resource may use role `Started` on a node only when
   that node is online at durable generation, stickiness matches the fold, and
   no unretracted fence for that node has `epoch` strictly greater than the
   resource `start_epoch` recorded under `/var/lib/pacemaker/resources/`.
   Otherwise the role is `Stopped` (node may still be the planned home).

4. Abort-window residue under `/var/lib/cluster/ops/abort.d/` rematerializes
   into live CIB drop-ins on every seating pass unless
   `/var/lib/cluster/ops/state/cutover.ok` exists as plain `key=value` lines
   with exactly `gen=<target>` (matching `gen.target`) and `mode=seal`. A
   matching receipt skips rematerialize; it does **not** mean delete the live
   drop-in. `/etc/pacemaker/cib.d/90-local.conf` must remain present and carry
   site-standard tokens. The abort package itself stays forensic with its
   original synonym tokens.

5. The `fences` array publishes every unretracted row as
   `{target, epoch, status:"fenced"}` sorted by target then epoch. Retracted
   history does not appear.

6. Two sequential seating runs must leave byte-identical
   `/output/crm-seat.json`.
