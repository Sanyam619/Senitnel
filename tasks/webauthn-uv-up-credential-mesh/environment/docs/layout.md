Ceremony Layout
===============

Live host trees

- `/etc/ceremony/site_standard.conf` — site-standard policy tokens
- `/etc/ceremony/reconcile.d/*.conf` — drop-ins folded in lexical order
- `/etc/ceremony/reconcile.conf` — effective folded policy (authority plane)

- `/var/lib/ceremony/state/uv_policy.conf` — UV/UP profile requirements
- `/var/lib/ceremony/state/hold_bound` — ledger hold bound seating
- `/var/lib/ceremony/state/stream.order` — credential/WAL stream seating
- `/var/lib/ceremony/state/gen.target` — target generation for cutover
- `/var/lib/ceremony/state/cutover.ok` — durable sealed cutover receipt
- `/var/lib/ceremony/ops/abort.d/` — forensic abort-window drop-in residue

Operator tools

- `/app/ops/run_mesh.sh` — mesh entrypoint (seats helpers, publishes ledger)
- `/app/ops/seat_uv.sh` — UV/UP policy seating
- `/app/ops/axle_hold.sh` — hold-bound seating
- `/app/ops/knit_stream.sh` — stream-order seating
- `/app/ops/fold_d.sh` — abort rematerialize + drop-in fold
- `/app/ops/emit_mesh.sh` — invoke prebuilt evaluator
- `/app/ops/ceremonyd_health` — surface health (not deep authority)

Binaries

- `/app/bin/trusteval` — deep admission publisher
- `/app/bin/jarcheck` — surface attestation copy (false-green bait)
- `/usr/lib/ceremony/bin/trusteval` and `/usr/lib/ceremony/bin/jarcheck` — sealed restore copies

Temporary verifier staging files under `/tmp/` may use names such as
`out-second.json`, `out-reentry.json`, `out-dynamic.json`, `out-forged.json`,
and `out-legacy.json`.

Data

- `/app/data/credentials/*.jsonl` — lane credential feeds
- `/app/data/signed_segments/*.bin` — WAL segment bins
- `/app/data/manifests/` — authority-class watermark/seed sheets
- `/app/data/ledger/revocations.jsonl` — hold/revoke ledger
- `/app/data/fixtures/` — surface fixture, audit samples (`domain_ascii=WAUV`), dynamic frames
- Verifier may stage `/app/data/signed_segments/seg_97.bin`, `seg_98.bin`, `seg_99.bin`

Docs

- `/app/docs/ceremony_outcomes.md` — graded seating scenarios
- `/app/docs/layout.md` — this path map

Packaged seeds under `/app/config/` mirror drop-ins and site-standard for
operators who re-copy into the live trees.
