Seating Contract
================

Graded seating produces `/output/postfix-seat.json`:

- `schema_tag` must be the literal string `postfix-seat-v1`
- `instances` lists every roster name with `queue_dir` (string),
  integer `generation`, and boolean `active`
- `transports` lists every pattern from the folded prefer nexthop map
  with `nexthop` (string) and boolean `honored`
- `seat_ok` is true only when every roster instance agrees with durable
  authority (tip queue_dir, journal admit without revoke, floor gate),
  transport patterns carry durable nexthops with abort-fragment honor
  polarity, live master.d carries site-standard tokens, live instance
  `main.cf` selects the prefer nexthop map (not the live decoy), the
  preference mode is `durable` or `authority`, and tip bind acceptance
  matches `gen.target`. Agreement means each instance carries its
  durable verdict — a correct seat reports `seat_ok` true even though
  revoked or below-floor instances carry `active=false`. Universal
  activation is not required and is not correct for this desk.

Preference
----------

A durable seat requires `/var/lib/postfix/ops/prefer.toml` mode
`durable` or `authority`. Seating reads that file as already set for the
current pass and must not overwrite the mode while seating runs. Modes
`live` and `surface` keep the desk on surface tip and nexthop-map
materials under `/var/lib/postfix/surface/`. Durable or authority
preference restores the working map
`/var/lib/postfix/ops/maps/nexthop.prefer` from the durable authority
copy `/var/lib/postfix/ops/maps/nexthop.durable` before transport fold.
Surface rematerialize may overwrite the working prefer map; it must not
overwrite `nexthop.durable`. Tip bind acceptance at
`/var/lib/postfix/ops/tip_bind.accept` must carry `gen=<gen.target>` for a
durable seat to stick across rematerialize. After an operator flips
preference to live or surface and reseats, `seat_ok` is false while
surface materials are in play. Flipping preference back to durable or
authority and reseating must recover `seat_ok` true with durable
instance and transport verdicts.

Outcomes
--------

- Durable prefer tips live in `/var/lib/postfix/ops/prefer.jsonl`. The
  authoritative batch is the latest `sealed` and `complete` batch whose
  `gen` matches `/var/lib/postfix/state/gen.target`. Incomplete later
  batches are not selected, and an earlier revision of the target
  generation is superseded by a later one. After apply, `gen.live`
  equals `gen.target`, and each instance tip is recorded as
  `/var/lib/postfix/state/tip_<name>.gen` and `tip_<name>.queue`.
- Durable floors live under `/var/lib/postfix/floors/<name>.floor`. A tip
  generation at or above that floor may be in service (equality
  inclusive). Live sheets under `/etc/postfix/floors/` are not authority.
- Instance journal `/var/lib/postfix/ops/instances.jsonl` admit/revoke
  rows gate journal eligibility for the sealed generation.
- Transport maps fold from the working prefer nexthop map under
  `/var/lib/postfix/ops/maps/nexthop.prefer` after preference-gated
  rematerialize or durable restore. Live decoy map
  `/etc/postfix/maps/nexthop.live` is not authority. Each live instance
  `main.cf` must set `transport_maps` to the prefer map path.
- Abort fragments under `/var/lib/postfix/ops/abort.d/` contribute
  transport patterns. A pattern that appears in the prefer map and also
  collides with a later abort fragment is reported with `honored=false`.
  Patterns without an abort collision keep `honored=true`.
- Abort residue rematerializes into live master.d unless
  `/var/lib/postfix/state/cutover.ok` already matches as plain
  `key=value` with `gen=<target>` and `mode=seal`. A matching receipt
  skips rematerialize; it does not mean delete the live drop-in. Within
  one successful seating pass those steps are ordered: abort
  rematerialize may run first when the receipt does not match, then
  seating installs site-standard tokens from
  `/app/config/site_standard.conf` into live `90-local.cf` so the live
  drop-in does not remain on abort residue (`prefer_abort`), and seating
  emits `/var/lib/postfix/state/cutover.ok` with `gen=<gen.target>` and
  `mode=seal`. Live `90-local.cf` must remain present. The abort
  package itself stays forensic.
- An instance is `active=true` only when tip queue_dir is applied on the
  live instance tree, tip generation ≥ durable floor, and the name is
  journal-eligible.
- Each instance `queue_dir` must be the durable tip path from the sealed
  prefer batch (not a surface or live decoy spool path).
