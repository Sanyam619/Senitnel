# Column stripe files

Stripes are the immutable base storage unit. Each namespace keeps its stripes
under `/app/data/columns/` as `{namespace}_{id}.col`, with the stripe id
zero-padded to three digits. Merge outputs produced by compaction use stripe
id `99` and are written to `{namespace}_merged.col`.

A stripe file is a single JSON document:

```json
{"id": 7, "records": [{"k": "…", "v": 0, "t": 0}]}
```

- `k` — record key (ASCII, unique within one stripe)
- `v` — signed 64-bit integer payload
- `t` — unsigned write timestamp

## Which stripes are readable

A stripe file on disk is not by itself part of any readable view. The set of
stripes that make up a namespace at a given journal generation is defined
solely by the manifest journal entry for that generation (see
`manifest_journal.md`). Compaction and garbage collection routinely leave
stripe files on disk that no longer belong to any current stripe set, and
merge outputs appear on disk before the journal entry that admits them is
durable.

## Duplicate keys across stripes

Within one manifest entry, the `stripes` list is ordered oldest to newest.
When the same key occurs in more than one stripe of the entry, the record
from the stripe listed later supersedes records from stripes listed earlier.
The list order is authoritative; stripe id values carry no ordering meaning.
