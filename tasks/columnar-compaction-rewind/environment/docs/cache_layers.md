# Derived caches and runtime state

Two kinds of derived state live next to the base data. Both are rebuilt from
stripes and the journal during normal operation and are only advisory.

## Sidecar indexes

`/app/data/sidecars/{namespace}.idx` holds a key-to-stripe lookup cache with
the generation it was built at (`bound_gen`), a key map, and a digest over
the stripe bytes it indexed. Sidecars are refreshed lazily and lag the
journal; after an unclean shutdown they can be bound to a generation that is
several compaction cycles old, and their maps can reference stripe sets that
are no longer part of any consistent generation.

## Boot state snapshot

`/app/data/state/last_boot.json` is the node's periodically flushed runtime
snapshot: node id, whether the last shutdown was clean, the generation the
runtime considered active, and the highest WAL sequence it had assigned. The
snapshot is flushed ahead of durability barriers, so after a crash the
`active_gen` and `wal_seq` it reports routinely run ahead of what the journal
and WAL can actually support.
