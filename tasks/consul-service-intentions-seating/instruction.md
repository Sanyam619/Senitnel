Live Consul agent materials under `/etc/consul.d/` and durable operations state
under `/var/lib/consul/ops/` disagree after an aborted mesh rollout, so the
catalog seats services on the wrong nodes and the mesh answers with the wrong
allow/deny decisions. Surface `/usr/local/bin/consulhealth` reads TTL check
files only and can report catalog-passing while deep seating is wrong. Frozen
service definitions under `/app/data/consul/` are integrity-pinned; do not
rewrite them. The prebuilt publisher `/app/publisher/consulseat` is pinned the
same way and must not be edited. Seating starts at
`/app/ops/run_consul_seat.sh` and publishes through that publisher. Records
under `/app/docs/` expand the definition, batch, floor, and journal formats.

Write `/output/consul-seat.json` with schema_tag, services, intentions, and
seat_ok. Each services entry carries name, node, generation, and registered.
Each intentions entry carries source, destination, action, and honored.
schema_tag must be consul-seat-v1. Types are string, string, integer, boolean
for services and string, string, string, boolean for intentions.

What the seated mesh has to satisfy:

- The seated node for a service comes from the full lexical fold of
  `/etc/consul.d/conf.d/`. Later drop-ins override earlier bindings for the
  same service, a pinned binding is never overridden by a later drop-in, and a
  drop record clears a binding so the frozen definition's node applies again.
- The catalog tip is the durable batch with the highest generation that is
  both sealed and complete and is not named in the superseded list. Unsealed,
  incomplete, and superseded batches are never selected, and mirror copies are
  not authority. The generation of the selected batch is written to
  `/var/lib/consul/ops/state/generation.live`.
- A service is registered only when the catalog tip carries a row for it, the
  seated node equals that row's node, and that row's generation is at or above
  the service floor. Services failing any of those report registered false with
  their seated node and tip generation; they are not to be forced true by
  editing definitions, floors, or durable batches.
- Intention pairs and their allow/deny action come from the durable preference
  batch whose generation equals the selected catalog generation. The live
  `/etc/consul.d/intentions.d/` sheet is a default-allow surface, not authority.
- An intention is honored only when the sealed journal still holds an
  unretracted commit for that exact pair and both endpoints are registered. A
  retraction cancels the commit with the matching event id only, so a pair with
  a second commit stays honored.
- Rollback residue under `/var/lib/consul/ops/abort.d/90-local.hcl`
  rematerializes into live `/etc/consul.d/conf.d/90-local.hcl` on every seating
  pass unless `/var/lib/consul/ops/state/cutover.ok` carries
  `gen=<generation.target>` and `mode=seal`. A matching receipt skips
  rematerialize; it does not delete the live drop-in, and the rollback package
  stays forensic. Under a matching receipt the live drop-in carries the
  site-standard tokens from `/app/config/site_standard.conf`. A stale or missing
  receipt leaves rollback bindings live for that pass. A completed seating pass
  records that receipt itself as `gen=<generation.target>` and `mode=seal`.
- Deep registration ownership lands in `/etc/consul.d/runtime/catalog.map`, one
  `name=node` line per registered service, sorted. Surface token maps are not
  authority.
- seat_ok is true only when the published ledger agrees with durable authority
  and the current seal is recorded. Two seating passes must leave
  `/output/consul-seat.json` byte-identical.
