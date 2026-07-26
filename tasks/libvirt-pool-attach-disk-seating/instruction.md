A host crash left our VM storage half-seated. The live definitions under
`/etc/libvirt/storage/` and `/etc/libvirt/qemu/` drifted from the durable
authority under `/var/lib/libvirt/`, and `/var/run/libvirt/` still holds torn
lease markers. The operator entrypoint `/app/ops/run_pool_attach.sh` runs, but
`/output/libvirt-attach.json` comes out inconsistent and the disks it should
seat stay down. `/usr/local/bin/virthealth` may print a healthy line over this
wrong state.

Recovery starts at `/app/ops/run_pool_attach.sh`. Docs under `/app/docs/`
describe the normal layout and the durable authority under
`/var/lib/libvirt/ops/`. The prebuilt reconcile engine lives under `/app/bin/`.

Bring seating back. The entrypoint must write `/output/libvirt-attach.json`. The
report is JSON with a schema_tag string; a pools array whose objects carry name,
path, uuid, and state; a disks array whose objects carry domain, target, source,
pool, and attached; and a top-level attach_ok boolean. Only the pools and disks
named by the in-scope roster under `/etc/libvirt/qemu/` may appear in either. A
disk seats only where three surfaces coincide: its pool brought up at the
durable target path, its domain definition bound to the pool's durable identity
in place of the drifted surface definition, and a key=value cutover receipt on
file. Surface pool definitions carry decoy identities.

The volume fixtures under `/app/data/pools/` must stay byte-for-byte identical.
Two sequential runs of the entrypoint must leave an identical
`/output/libvirt-attach.json`.
