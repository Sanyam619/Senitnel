Seating Contract
================

Graded seating produces `/output/dhcp-seat.json`:

- `schema_tag` must be the literal string `dhcp-seat-v1`
- `subnets` lists every roster subnet with integer `id`, string `pool`
  (CIDR), and integer `generation`
- `reservations` lists every folded reservation with `hw`, `ip`, integer
  `subnet`, and boolean `honored`
- `conflicts` lists every rejected allocation as `{ip, reason}` where
  `reason` is one of `duplicate_ip`, `lease_collision`, `generation_floor`,
  `pool_miss`, `shadowed`
- `seat_ok` is true only when every reservation honor flag and every
  conflict row agree with durable authority
- Row order inside `reservations` and `conflicts` is not graded; any order
  is accepted when the multiset of rows is correct
- Each subnet `generation` in the ledger is the sealed journal tip value
  for that subnet id (the raw tip generation from the sealed cutover),
  not a live floor sheet and not a clamped or remapped substitute

Activity rules
--------------

1. Durable pool preference lives at `/var/lib/kea/ops/prefer.toml` as
   `pool_root=durable`. When `pool_root` is anything else, live decoy
   pools under `/etc/kea/pools/` are consulted instead. Durable subnet
   pools live under `/var/lib/kea/pools/<id>.pool` as a single CIDR line.

2. Durable floors live under `/var/lib/kea/floors/<id>.floor` as a single
   integer. A tip generation at or above that floor may be in service
   (equality inclusive). Live sheets under `/etc/kea/floors/` are not the
   durable authority.

3. Graded fold input is the live drop-in directory
   `/etc/kea/kea-dhcp4.d/`. Files fold in lexical filename order; later
   files override earlier `reserve.<hw>` lines and site tokens. An
   `abort=<token>` value from a later drop-in is residual policy noise
   that must not survive a successful cutover into live `90-local.conf`.
   A reservation for the same `hw` that is overridden by a later drop-in
   is `shadowed` and must not be honored; emit a conflict on its prior
   `ip` with reason `shadowed`.

4. A reservation is honored only when all of the following hold:
   - its `ip` is inside the durable-preferred subnet pool for its
     `subnet` id
   - that subnet's tip generation is at or above its durable floor
   - the sealed memfile under `/var/lib/kea/ops/memfile.csv` does not
     already lease that `ip` to a different `hw`
   - it is not shadowed by a later conf.d drop-in
   - no other folded reservation claims the same `ip` (duplicates are
     never honored; each conflicting `ip` appears once in `conflicts`
     with reason `duplicate_ip`)

5. Abort-window residue under `/var/lib/kea/ops/abort.d/` rematerializes
   into live kea-dhcp4.d on every seating pass unless
   `/var/lib/kea/state/cutover.ok` is a matching receipt. A matching
   receipt is plain `key=value` lines with exactly `gen=<target>`
   (matching `/var/lib/kea/state/gen.target`) and `mode=seal`. Receipt
   polarities:
   - matching (`gen` equals target and `mode=seal`) skips rematerialize
   - wrong-gen (`gen` differs from target) rematerializes abort
   - wrong-mode (`mode` is anything other than `seal`) rematerializes
     abort
   A matching receipt does **not** mean delete the live drop-in.
   `/etc/kea/kea-dhcp4.d/90-local.conf` must remain present and carry
   site-standard tokens from `/app/config/site_standard.conf`
   (`tip_policy`, `bind_order`, and `reserve.<hw>` lines). The abort
   package itself stays forensic with its original synonym tokens.

6. Ops journal under `/var/lib/kea/ops/journal.jsonl` records cutover tip
   generations. The sealed cutover for `gen.target` is authoritative;
   after apply, `gen.live` equals `gen.target` and each `tip_<id>.gen`
   matches the journal tip for that subnet id. Those tip values are what
   appear as subnet `generation` in `/output/dhcp-seat.json`.

7. Sealed memfile rows are `ip,hw,state` CSV lines. Only `state=active`
   rows participate in lease continuity.
