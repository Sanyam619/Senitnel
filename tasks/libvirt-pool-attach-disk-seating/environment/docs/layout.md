# Virtualization host layout

This host seats VM storage using a small reconciler around the libvirt-style
definition tree.

## Definition surfaces (live)

- `/etc/libvirt/storage/pool_<name>.xml` — storage pool definitions. Each carries
  a `<name>`, a `<uuid>`, and a `<target><path>`.
- `/etc/libvirt/qemu/<name>.xml` — domain definitions. Each disk binds a pool by
  `<source pool='..' uuid='..' volume='..'/>` and a `<target dev='..'/>`.
- `/etc/libvirt/qemu/seat.roster` — the disks that are in scope, one
  `domain|target|pool|volume` per line.
- `/etc/libvirt/qemu/attach.d/*.conf` — selection drop-ins (see below).
- `/etc/libvirt/storage/attach.seal` — the sealed generation cap.

## Durable authority

- `/var/lib/libvirt/ops/cutover.journal` — the canonical record of each pool's
  bound identity and target path across generations, one
  `gen|seq|pool|uuid|path` per line. The definition files under `/etc/libvirt`
  are convenience surfaces and can drift from this record after a crash.
- `/var/lib/libvirt/ops/receipts/` — cutover receipts, one per seated disk.
- `/var/lib/libvirt/storage/<pool>/pool.state` — runtime pool state.

## Runtime

- `/var/run/libvirt/` — per-request locks and lease markers.
- `/app/data/pools/` — read-only volume fixtures. These are frozen inputs.

## Tools

- `/app/ops/run_pool_attach.sh` — the operator entrypoint.
- `/app/bin/virtattach` — the sealed reconcile engine invoked by the entrypoint.
- `/usr/local/bin/virthealth` — a surface probe that only counts definition
  files; it does not inspect seating outcomes.
