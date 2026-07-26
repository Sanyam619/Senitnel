Live Keepalived VRRP seating under `/etc/keepalived/` and durable operations
state under `/var/lib/keepalived/ops/` drifted following an abort-window cutover.
Surface `/usr/local/bin/vrrphealth` may print MASTER-OK with deep seating wrong.
Frozen peer fixtures under `/app/data/vrrp/` are integrity-pinned; do not rewrite
them. The prebuilt publisher `/app/publisher/vrrpseat` is also integrity-pinned
and must not be modified. Operator seating starts at `/app/ops/run_vrrp_seat.sh`
and publishes through that publisher. Docs under `/app/docs/` expand weight
records, journals, track probes, and seating scenarios.

Write `/output/vrrp-seat.json` with schema_tag, instances, transitions, and
seat_ok. Each instances entry carries name, vrid, state, priority, vip, and
generation. Each transitions entry carries vrid, epoch, from, and to.
schema_tag must be vrrp-seat-v1.

Scenarios the desk must satisfy:

- For each VRID, at most one eligible peer may hold MASTER. Different VRIDs may
  legitimately seat different MASTER peers at the same time.
- Effective priority comes from the full lexical conf.d fold, then track-script
  weight sheets that apply for probes with status UP.
- Preference tips come from the latest sealed and complete durable batch.
  Incomplete later batches are not selected. The generation of that selected
  batch is written to `/var/lib/keepalived/ops/state/generation.live`.
- On a priority tie between two eligible peers on one VRID, the durable
  preference rank breaks the tie and the higher rank wins.
- Eligibility requires an inactive hold (hold expiry strictly greater than the
  desk clock means active), tip at or above the peer floor, and interface
  generation at or above that same floor.
- A committed unretracted movement whose from state is MASTER vetoes MASTER for
  that VRID. Retractions cancel the matching event id only.
- Abort residue under `/var/lib/keepalived/ops/abort.d/` rematerializes into
  live conf.d on every seating pass unless `/var/lib/keepalived/ops/state/cutover.ok`
  matches the generation target with mode=seal. A matching receipt skips
  rematerialize; it does not delete the live drop-in. The abort package stays
  forensic. Site-standard tokens from `/app/config/site_policy.conf` apply to
  live `/etc/keepalived/conf.d/90-local.conf` under a matching seal receipt.
  A stale or missing receipt rematerializes abort into the live drop-in for that
  pass; site-standard tokens do not override abort on a mismatch. On a successful
  seating pass the pipeline writes that receipt itself: `gen=<generation.target>`
  and `mode=seal` into `/var/lib/keepalived/ops/state/cutover.ok`.
- Deep VIP ownership is recorded under `/etc/keepalived/runtime/advert.map`, one
  `vip=peer` line per current MASTER, sorted. Surface token maps are not durable
  authority.
- seat_ok is true only if the ledger agrees with durable authority and the
  single-master-per-VRID rule. Two seating runs must leave `/output/vrrp-seat.json`
  byte-identical.
