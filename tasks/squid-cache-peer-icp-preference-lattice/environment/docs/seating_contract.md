Seating Contract
================

Graded seating produces `/output/squid-seat.json`:

- `schema_tag` must be the literal string `squid-seat-v1`
- `peers` lists every roster name with `host` (string), `type`
  (`parent` or `sibling`), integer `weight`, integer `generation`,
  and boolean `selected`
- `acls` lists every ACL name from the folded conf.d sheet with boolean
  `matched` (`match` → true, `skip` → false)
- `seat_ok` is true only when every roster peer agrees with durable
  authority (tip type/weight, journal admit without revoke, floor gate,
  ACL abort set), live `90-local.cfg` carries site-standard tokens, the
  preference mode is `durable` or `authority`, and tip bind acceptance
  matches `gen.target`. Agreement means each peer carries its durable
  verdict — a correct seat reports `seat_ok` true even though revoked,
  below-floor, or aborted peers carry `selected=false`. Universal
  selection is not required and is not correct for this desk.

Preference
----------

`/var/lib/squid/ops/prefer.toml` must settle on `durable` or `authority`.
Modes `live` and `surface` keep the desk on surface tip and peer-sheet
materials under `/var/lib/squid/surface/`. Tip bind acceptance at
`/var/lib/squid/ops/tip_bind.accept` must carry `gen=<gen.target>` for a
durable seat to stick across rematerialize.

Outcomes
--------

- Durable prefer tips live in `/var/lib/squid/ops/prefer.jsonl`. The
  authoritative batch is the latest `sealed` and `complete` batch whose
  `gen` matches `/var/lib/squid/state/gen.target`. Incomplete later
  batches are not selected, and an earlier revision of the target
  generation is superseded by a later one. After apply, `gen.live`
  equals `gen.target`, and each peer tip is recorded as
  `/var/lib/squid/state/tip_<name>.gen`, `tip_<name>.type`, and
  `tip_<name>.weight`.
- Durable floors live under `/var/lib/squid/floors/<name>.floor`. A tip
  generation at or above that floor may be in service (equality
  inclusive). Live sheets under `/etc/squid/floors/` are not authority.
- Peer journal `/var/lib/squid/ops/peers.jsonl` admit/revoke rows gate
  journal eligibility for the sealed generation.
- conf.d drop-ins fold ACL keys last-writer-wins and abort names as a
  union. Residual abort policy does not survive a successful cutover
  into live `90-local.cfg`.
- Abort residue under `/var/lib/squid/ops/abort.d/` rematerializes into
  live conf.d unless `/var/lib/squid/state/cutover.ok` already matches
  as plain `key=value` with `gen=<target>` and `mode=seal`. A matching
  receipt skips rematerialize; it does not mean delete the live
  drop-in. Within one successful seating pass those steps are ordered:
  abort rematerialize may run first when the receipt does not match,
  then seating installs site-standard tokens from
  `/app/config/site_standard.conf` into live `90-local.cfg` so the live
  drop-in does not remain on abort residue (`prefer_abort`), and seating
  emits `/var/lib/squid/state/cutover.ok` with `gen=<gen.target>` and
  `mode=seal`. Live `90-local.cfg` must remain present. The abort
  package itself stays forensic.
- A peer is `selected=true` only when tip type/weight are applied on the
  live peer sheet, tip generation ≥ durable floor, the peer is
  journal-eligible, and the name is not in the folded abort set.
- Each peer `host` must be the durable address from
  `/var/lib/squid/peers/<name>.host`.
