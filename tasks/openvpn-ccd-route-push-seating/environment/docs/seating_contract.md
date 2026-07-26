Seating Contract
================

Graded seating produces `/output/ovpn-seat.json`:

- `schema_tag` must be the literal string `ovpn-seat-v1`
- `clients` lists every roster CN with string `iroute`, integer
  `generation`, and boolean `pushed`
- `pools` lists every durable pool with string `cidr` and boolean `active`
- `seat_ok` is true only when every roster client agrees with durable
  authority (tip iroute, journal admit without revoke, floor gate,
  abort set), the prefer-selected pool is the only overlapping active
  pool, live `90-local.conf` carries site-standard tokens, the
  preference mode is `durable` or `authority`, and tip bind acceptance
  matches `gen.target`. Agreement means each client carries its durable
  verdict — a correct seat reports `seat_ok` true even though revoked,
  below-floor, or aborted clients carry `pushed=false`. Universal push
  is not required and is not correct for this desk.

Preference
----------

`/var/lib/openvpn/ops/prefer.toml` must settle on `durable` or `authority`.
Modes `live` and `surface` keep the desk on surface tip and CCD
materials under `/var/lib/openvpn/surface/`. Tip bind acceptance at
`/var/lib/openvpn/ops/tip_bind.accept` must carry `gen=<gen.target>` for a
durable seat to stick across rematerialize.

Outcomes
--------

- Durable prefer tips live in `/var/lib/openvpn/ops/prefer.jsonl`. The
  authoritative batch is the latest `sealed` and `complete` batch whose
  `gen` matches `/var/lib/openvpn/state/gen.target`. Incomplete later
  batches are not selected, and an earlier revision of the target
  generation is superseded by a later one. After apply, `gen.live`
  equals `gen.target`, and each client tip is recorded as
  `/var/lib/openvpn/state/tip_<cn>.gen` and `tip_<cn>.iroute`.
- Durable floors live under `/var/lib/openvpn/floors/<cn>.floor`. A tip
  generation at or above that floor may be in service (equality
  inclusive). Live sheets under `/etc/openvpn/server/floors/` are not
  authority.
- Client journal `/var/lib/openvpn/ops/clients.jsonl` admit/revoke rows
  gate journal eligibility for the sealed generation.
- Durable pools live in `/var/lib/openvpn/ops/pools.toml`. Exactly one
  prefer-selected pool may be `active` among overlapping CIDRs; the live
  overlapping decoy must stay inactive when preference is durable.
- server conf.d drop-ins fold pool keys last-writer-wins and abort names
  as a union. Residual abort policy does not survive a successful
  cutover into live `90-local.conf`.
- Abort residue under `/var/lib/openvpn/ops/abort.d/` rematerializes into
  live conf.d unless `/var/lib/openvpn/state/cutover.ok` already matches
  as plain `key=value` with `gen=<target>` and `mode=seal`. A matching
  receipt skips rematerialize; it does not mean delete the live
  drop-in. Within one successful seating pass those steps are ordered:
  abort rematerialize may run first when the receipt does not match,
  then seating installs site-standard tokens from
  `/app/config/site_standard.conf` into live `90-local.conf` so the live
  drop-in does not remain on abort residue (`prefer_abort`), and seating
  emits `/var/lib/openvpn/state/cutover.ok` with `gen=<gen.target>` and
  `mode=seal`. Live `90-local.conf` must remain present. The abort
  package itself stays forensic.
- A client is `pushed=true` only when tip iroute is applied on the live
  CCD sheet, tip generation ≥ durable floor, the client is
  journal-eligible, and the CN is not in the folded abort set.
- Each client `iroute` must be the durable tip string from the selected
  prefer batch.
