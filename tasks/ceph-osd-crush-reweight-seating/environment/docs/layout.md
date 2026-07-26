# Desk layout

Normal layout of the placement desk on this host.

## Live materials

- `/etc/ceph/ceph.conf` — baseline cluster configuration.
- `/etc/ceph/reweight.d/osd.N.conf` — one live reweight sheet per device,
  `reweight_milli = <int>` in thousandths.
- `/etc/ceph/pools.d/*.conf` — live group sheets. Each `[pool "<name>"]`
  block carries `size`, `pg_num`, and a `state` annotation written by the
  monitor during earlier shifts.

## Durable plane (`/var/lib/ceph/ops/`)

- `crushmap.bin` — the packed durable placement image: an 8-byte magic
  (`CRUSHB1` plus a NUL) followed by a gzip stream of row text.
- `prefer.toml` — the desk's material preference (`plane` under `[source]`).
- `surface.map` — a working sheet captured from the surface plane during
  the last shift.
- `record.jsonl` — sealed copy of the device in/out record stream.
- `window.jsonl` — sealed copy of the maintenance window ledger.
- `now.mark`, `gen.low`, `gen.aim` — the desk clock, the acceptance floor,
  and the cutover aim.
- `state/` — the desk's scratch plane (per-device rows, flags, receipts,
  `gen.live`).

## Frozen fixtures (`/app/data/`)

- `crush/crush_map.txt` — the row-text mirror of the packed image.
- `ceph/` — device specs, group specs, the out-journal, the maintenance
  holds, and the captured epochs sheet.
- Digests are pinned in `/app/packaging/fixtures.sha256`. Nothing under
  `/app/data/` may change.

## Desk helpers

- `/app/ops/run_crush_seat.sh` — the seating entrypoint.
- Stage helpers live under `/app/ops/`, `/app/lane/`, `/app/mast/`, and
  `/app/deck/`.
- `/usr/local/bin/cephhealth` — surface monitor. `/app/bin/mapprobe` —
  packed-image header probe.

## Report

- `/output/crush-seat.json` — the placement report the desk emits.
