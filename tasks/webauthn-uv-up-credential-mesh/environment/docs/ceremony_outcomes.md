Ceremony Outcomes
=================

Deep admission for the UV/UP ceremony mesh is published by the prebuilt
evaluator under `/app/bin/trusteval` after live seating under `/etc/ceremony/`
and `/var/lib/ceremony/`. Surface `/app/ops/ceremonyd_health` (and
`/app/bin/jarcheck`) can look healthy while deep tallies disagree.

UV / UP seating
---------------

Credential JSONL rows may carry `uv` and `up` bits (0 or 1). Rows that omit
those fields behave as if both bits are set. Integrity-accepted WAL frames
count as both bits set. Live `/var/lib/ceremony/state/uv_policy.conf` names
per-profile requirements (`fleet_a_*` / `fleet_b_*`). Frames that miss a
required bit for the profile that owns the epoch do not raise `accepted` and
do not activate backends.

Hold vs revoke co-presence
--------------------------

A required lane that is only revoked does not keep the epoch published. A
required lane that is held (suspended) does: the epoch stays published under
its profile with reduced accepted (held frames do not raise the tally).
Ledger hold thresholds honor the live hold bound seating: exclusive seating
leaves the on-boundary credential usable; inclusive seating holds it.

Watermark
---------

Deep watermarks include the boundary timestamp. Credentials beyond the
watermark for an epoch do not contribute.

Interleaved replay
------------------

Within each epoch-and-lane stream, integrity-accepted WAL frames and
credential JSONL frames form one ascending-timestamp stream. Equal timestamps
order the WAL frame first. A frame whose timestamp does not strictly advance
the running maximum is excluded from accepted. Excluded WAL frames appear in
quarantine as `replay`; excluded credential frames are dropped from the tally
only. Live `/var/lib/ceremony/state/stream.order` must seat the interleaved
ascending mode; a JSONL-then-WAL seating skips the shared cross-stream fence.

Cutover receipt vs abort rematerialize
--------------------------------------

Abort-window residue under `/var/lib/ceremony/ops/abort.d/` rematerializes
into live `/etc/ceremony/reconcile.d/90-local.conf` on every mesh pass unless
a durable cutover receipt exists at `/var/lib/ceremony/state/cutover.ok`.
The receipt is plain `key=value` text with `mode=seal` and a `gen` that
matches `/var/lib/ceremony/state/gen.target`. A matching receipt skips the
abort copy; it does not mean delete the live drop-in. After a sealed cutover,
live `90-local.conf` must remain present and carry site-standard tokens from
`/etc/ceremony/site_standard.conf` (rewrite live synonyms in place). The abort
package itself stays forensic with abort tokens. Effective authority is the
lexically folded `/etc/ceremony/reconcile.conf`; surface authority selects the
wrong roster for deep admission.

Quarantine reasons
------------------

- `integrity_failure` — WAL signature fails under deep authority
- `replay` — WAL frame excluded by the interleaved monotonic fence
- `revoked` — WAL frame rejected by the revocation ledger

Publish both `/output/ceremony-ledger.json` and `/output/quarantine.json`
through `/app/ops/run_mesh.sh`. Hand-written stand-ins that ignore live
seating fail re-entry.
