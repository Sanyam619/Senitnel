Intention records
=================

Preference batches
------------------

`/var/lib/consul/ops/prefer.jsonl` holds one JSON object per line with
`kind=batch`, a string `id`, an integer `gen`, booleans `sealed` and `complete`,
and a `rows` array of `{source, destination, action}` objects. `action` is
`allow` or `deny`. Preference batches are published alongside catalog batches
and are read by generation: the batch that belongs to the catalog generation the
pass selected is the one that describes the mesh, and the other batches on disk
belong to other generations.

Journal rows
------------

`/var/lib/consul/ops/intents.jsonl` holds the sealed intention journal:

- `kind=commit` carries `eid`, `source`, `destination`, and `epoch`
- `kind=retract` carries `eid` and `epoch`

A retraction cancels the commit with the matching `eid`. Nothing else is
cancelled by it — other commits from the same source, and other commits for the
same pair, keep standing. Pairs are committed more than once over a rollout, so
a pair can survive a retraction through a later commit.

Surface mesh sheet
------------------

`/etc/consul.d/intentions.d/*.hcl` carries `default_action = <action>` and
`pair <source> <destination> = <action>` lines. The local agent renders this
sheet from whatever it last accepted, which after an aborted rollout is the
permissive default. It is a display of the surface, not the preference
authority.

Scenario: the surface sheet shows a pair as allow while the preference batch for
the selected generation denies it; the published action follows the batch.
Scenario: a pair holds an unretracted commit and still is not honored, because
one of its endpoints is not a registered service. Scenario: a pair was retracted
once and committed again afterwards, and it stays honored.
