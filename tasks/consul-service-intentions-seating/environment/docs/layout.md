Mesh desk layout
================

Live agent materials
--------------------

- `/etc/consul.d/consul.hcl` — agent settings for the lab datacenter.
- `/etc/consul.d/conf.d/*.hcl` — node binding drop-ins, folded in lexical
  filename order.
- `/etc/consul.d/intentions.d/*.hcl` — the surface mesh sheet the local agent
  renders. It carries a default action and one line per pair.
- `/etc/consul.d/runtime/catalog.map` — deep registration rows written after a
  seating pass, one `name=node` line per registered service.
- `/etc/consul.d/runtime/token.map` — surface token rows, one `name passing`
  line per known definition. Not durable authority.

Durable operations state
------------------------

- `/var/lib/consul/ops/roster.jsonl` — catalog batches.
- `/var/lib/consul/ops/superseded.list` — batch ids withdrawn by operations.
- `/var/lib/consul/ops/prefer.jsonl` — intention preference batches.
- `/var/lib/consul/ops/intents.jsonl` — the sealed intention journal.
- `/var/lib/consul/ops/floors/<name>.floor` — one integer per service.
- `/var/lib/consul/ops/abort.d/90-local.hcl` — rollback residue kept for
  forensics after the aborted rollout.
- `/var/lib/consul/ops/mirror/roster_mirror.jsonl` — an operator copy taken
  during the rollout window. Copies drift; they are not authority.
- `/var/lib/consul/ops/state/generation.target` — the generation operations is
  seating toward.
- `/var/lib/consul/ops/state/generation.live` — the generation of the batch the
  last pass actually selected.
- `/var/lib/consul/ops/state/cutover.ok` — the seal receipt, `key=value` lines.
- `/var/lib/consul/ops/extra/*.json` — optional additional service definitions
  staged by operations; they follow the same fold, tip, and eligibility path.

Work tables and tools
---------------------

`/app/ops/run_consul_seat.sh` refreshes the work tables under
`/var/lib/consul/ops/live/` and then publishes through
`/app/publisher/consulseat`. The publisher consumes those tables plus the frozen
definitions under `/app/data/consul/`; it does not read the drop-ins, the
batches, or the journal itself.

Work tables are tab separated:

- `bind.tsv` — `name`, seated node
- `tip.tsv` — `name`, catalog tip node, catalog tip generation
- `reg.tsv` — `name`, registration flag (`1` or `0`), tip node
- `acts.tsv` — `source`, `destination`, action
- `cmt.tsv` — `source`, `destination`, event id, epoch

`/usr/local/bin/seatpeek` prints the work tables and the state files.
`/usr/local/bin/consulhealth` summarises the TTL check files under
`/var/lib/consul/checks/` and nothing else — it never reads batches, floors,
the journal, or the seal receipt.

Definitions under `/app/data/consul/` and the publisher under
`/app/publisher/consulseat` are integrity-pinned in
`/app/packaging/consul.sha256` and must stay byte-identical.
