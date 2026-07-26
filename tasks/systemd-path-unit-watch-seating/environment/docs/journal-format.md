Preference and trigger journals
===============================

Durable watch tips live in `/var/lib/systemd/ops/prefer.jsonl` as JSON objects
with `kind=batch`, integer `gen`, booleans `sealed` and `complete`, and a `rows`
array of `{id, exists, changed, tip}` objects. Only a sealed and complete batch
is authoritative; among those, the highest `gen` wins. Incomplete or unsealed
later batches are not selected. Each row gives the expected `PathExists` and
`PathChanged` for that unit and an integer `tip` (the per-unit watch
generation). The selected batch `gen` is recorded in
`/var/lib/systemd/ops/state/generation.live`.

Trigger rows live in `/var/lib/systemd/ops/triggers.jsonl`:

- `kind=fire` carries `eid`, `unit`, `epoch`
- `kind=retract` carries `eid` and `epoch`

A retraction cancels the fire with the matching `eid` only. For each unit, the
last unretracted fire epoch is its `last_epoch`; a unit with no unretracted fire
has no trigger entry.

Floor files under `/var/lib/systemd/ops/floors/<unit>.floor` are a single
integer. Watch generation files under `/var/lib/systemd/ops/watchgen/<unit>.gen`
are a single integer. A unit may be armed only when its `tip` and its watch
generation are both at or above the floor.

Scenario: a unit may carry the expected watched paths yet stay unarmed when its
`tip` sits below the floor. Scenario: a unit whose watch generation sits below
the floor stays unarmed even at the authoritative tip. Scenario: a unit whose
folded `[Path]` block declares `DirectoryNotEmpty` is a directory-watch bait and
is never armed, even when its `PathExists` matches the tip. A trigger is honored
only when its unit is armed.
