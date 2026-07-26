Catalog records
===============

Service definitions
-------------------

Each file under `/app/data/consul/` holds one object with a `service` member
carrying `name`, `id`, `node`, `port`, and `tags`. The `node` member is the node
the definition was published for; it applies whenever no live drop-in binds that
service somewhere else.

Binding drop-ins
----------------

Files under `/etc/consul.d/conf.d/` are read in lexical filename order. Each
non-comment line is one of:

- `<name>.node = <node>` — bind that service to a node
- `pin <name>.node = <node>` — bind and hold the binding
- `drop <name>.node` — clear any binding recorded so far for that service

A later drop-in overrides an earlier binding for the same service. A pinned
binding is not overridden by a later drop-in, and a later `pin` for a service
that is not already pinned takes effect like a binding that then holds. After a
`drop` record the service has no live binding, so the definition's own node
applies unless a later drop-in binds it again. Keys that are not
`<name>.node` — for example `bind_order` or `tip_policy` — never enter the
binding table.

The sheets on this desk were written during the rack move and the rollout
window, so several of them move a service away from the node its definition was
published for: the zone sheet rebinds `delta` to `node-d9`, and the late node
sheet rebinds `epsilon` to `node-e7`.

Staged definitions
------------------

Operations can stage further definitions under
`/var/lib/consul/ops/extra/*.json` — for example a `kappa.json` publishing a
`kappa` service for `node-k1`. A staged definition folds, tips, and registers
on exactly the same path as a frozen one, and a drop-in may bind or pin it like
any other service.

Catalog batches
---------------

`/var/lib/consul/ops/roster.jsonl` holds one JSON object per line with
`kind=batch`, a string `id`, an integer `gen`, booleans `sealed` and `complete`,
and a `rows` array of `{name, node, gen}` objects. Row generations are per
service and are frequently older than the batch generation. Batch ids listed in
`/var/lib/consul/ops/superseded.list` were withdrawn; the list may also name ids
that no longer appear in the journal.

Floors
------

`/var/lib/consul/ops/floors/<name>.floor` is a single integer. A service that
carries a catalog tip row is at or above its floor when the row generation is
not smaller than the floor, so a row generation equal to the floor still clears
it.

Scenario: a service sits unregistered while `consulhealth` reports
catalog-passing, because the live drop-ins seated it on a node the catalog tip
does not carry. Scenario: a service is seated on the node the tip carries and
still stays unregistered, because the tip row for it predates its floor.
Scenario: a definition exists with no row in the selected batch at all; it
reports its seated node, generation zero, and no registration.
