# Manifest journal

The manifest journal records, per namespace, which stripe set is visible at
each journal generation. It is written as append-only JSONL tiers under
`/app/data/manifests/`: `tier_a.jsonl`, then `tier_b.jsonl`, then
`tier_c.jsonl`, in chronological order. Generations increase monotonically
across the tiers.

Each line is one entry:

```json
{"gen": 12, "ns": "…", "stripes": [3, 1], "sha256": {"1": "…", "3": "…"}}
```

- `gen` — journal generation the entry belongs to
- `ns` — namespace
- `stripes` — ordered stripe-id list (order semantics in `stripe_format.md`)
- `sha256` — lowercase hex SHA-256 of each listed stripe file's bytes,
  keyed by stripe id, recorded when the entry was committed

Not every generation carries an entry for every namespace. The stripe set of
a namespace at generation G is given by that namespace's entry with the
largest `gen` not exceeding G.

## Entry integrity

An entry is trustworthy only when every stripe file it lists is present on
disk and its bytes hash to the recorded `sha256` value. A mismatch or a
missing file means the entry describes state that never became durable, or
state whose files have since been collected; such an entry does not describe
a readable stripe set.

A generation is consistent when the resolved entry of every namespace is
trustworthy. Point-in-time reads are only defined at consistent generations.
