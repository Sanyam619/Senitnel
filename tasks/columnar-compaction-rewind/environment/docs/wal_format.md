# Write-ahead log

Changes accepted after the last compaction live in WAL segments under
`/app/data/wal/`, named `seg_NNN.bin` in creation order. All multi-byte
integers are little-endian. Every segment starts with a 5-byte header:
magic `WLOG` followed by a format version byte (`0x01`).

Records follow the header back to back. Each record starts with:

| field | size | notes |
|-------|------|-------|
| `seq` | 8 bytes | unsigned sequence number, unique per operation |
| `op`  | 1 byte  | `0x00` put, `0x01` delete, `0x02` checkpoint |

A checkpoint record ends there. Put and delete records continue with:

| field | size |
|-------|------|
| `ns_len` | 1 byte |
| `ns` | `ns_len` bytes, ASCII |
| `key_len` | 2 bytes |
| `key` | `key_len` bytes, ASCII |

A put record additionally carries:

| field | size | notes |
|-------|------|-------|
| `value` | 8 bytes | signed |
| `ts` | 8 bytes | unsigned |

## Reader semantics

- **Checkpoints and acknowledgement.** A checkpoint at sequence C means every
  operation with `seq <= C` was acknowledged to clients. Operations beyond
  the newest checkpoint anywhere in the log were never acknowledged, and a
  reader reconstructing a consistent view leaves them out.
- **Re-appended ranges.** After a broker reconnect, a segment may open by
  re-appending records that already exist at the tail of the previous
  segment. Re-appended records are byte-identical to the originals; the
  sequence number identifies an operation uniquely across all segments.
- **Torn tail.** A writer that dies mid-append leaves a final record whose
  declared lengths run past the end of the file. A conforming reader treats
  the segment as ending at the last complete record.
- **Ordering.** Operations apply in ascending sequence order regardless of
  which segment they were read from.
