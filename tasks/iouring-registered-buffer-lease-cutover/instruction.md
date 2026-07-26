The ingest broker lab under /etc/ingest and /var/lib/ingest is mid-cutover. Live unit files, durable lease maps, journal seal tips, preference drop-ins, abort-window isolation, and host vs broker mount trees disagree with the sealed cutover journal. Surface health checks may still report OK. Finish the ops cutover so roster tenants see fresh fixed-buffer registrations bound into the broker mount namespace under the durable lease epoch.

Operator recovery starts at /app/ops/run_cutover.sh. Docs under /app/docs/ describe normal layout. Prebuilt binaries live under /app/bin/.

Hand-applied end-state that is undone by the next recovery pass does not count. Durable recovery must leave /app/ops/run_cutover.sh able to complete again with matching broker slots, open unit policy across the live unit, live.d drop-ins, and abort-window fragments, a sealed durable plane, and a stable preflight stamp.

Bring the lab back so:

- The durable lease epoch and journal seal tip agree with the sealed cutover journal under the active seal cap, not the harbor diagnostic plane or a drifted profile sheet. The seal tip binds that epoch to the sealed slot prefix when cutover mode is sealed.
- Preference drop-ins under /etc/ingest/pref.d/ resolve to a seal-bound cutover preference for the materializer.
- Merged unit policy across /etc/ingest/units/live.service, every live.d drop-in, and abort-window fragments allows nested tenant seating; PrivateMounts isolation must not be left active. Unit-policy fold clears live-plane isolation drift; seating alone does not count as that repair. A sealed cutover receipt must suppress abort-window rematerialize of isolation.
- Tenant marker files exist under the broker mount tree and must not remain under /var/lib/ingest/mnt/host/ten/ for roster tenants.
- /var/lib/ingest/meta/activation.toml tip map matches roster tenants only after a successful pass; stale off-roster tip names from the crash must not remain.
- A second cutover pass, and two concurrent cutover jobs, leave matching broker slots, clean dual residency, and a stable preflight stamp. A preflight re-run on an already-correct lab must leave the lease map and buffer registry stable.
- Leave /var/lib/ingest/fixtures/seed alone.

Write /output/lease-cutover.json: version 1 and a tenants array. Each row needs tenant, buf_slot, mount_ns, lease_epoch, buf_fresh, and preflight_stable. buf_fresh and preflight_stable are JSON booleans. mount_ns is broker or host. lease_epoch is an integer matching the durable lease map. buf_slot is the on-disk registry slot id for that tenant: sealed slot_prefix, tenant name, and durable epoch joined by colons (matching the broker ring slot file body).
