Journal Formats (v1)
====================

All records use little-endian encoding. All widths are in bytes.

server_reclaim.log
------------------
Layout: [header 40][record*]

Header (40 bytes):
- magic[8]           = "NFSRSVR\0"
- version u32        = 1
- pad u32            = 0
- boot_epoch_prev u64
- boot_epoch_curr u64
- grace_window_ms u32
- reclaim_deadline_ms u32

Record header (3 bytes):
- tag u8
- length u16         (body length, not including these 3 bytes)

Record body (by tag):
- 0x01 RECLAIM_OPEN (56 bytes):
    client_id[16], open_owner[16], stateid_seq u64, fh[16]
- 0x02 RECLAIM_DELEG_WRITE (48 bytes):
    client_id[16], stateid_seq u64, fh[16], boot_epoch u64
- 0x03 RECLAIM_DELEG_READ  (48 bytes): same layout as 0x02
- 0x04 COMMIT_SEAL (24 bytes):
    seq u64, write_verifier[8], durable_bytes u64
- 0x05 NAMESPACE_OP (41 bytes):
    op u8 (1=rename, 2=unlink), src_fh[16], dst_fh[16], ts_ms u64
- 0x06 COPY_SESSION (41 bytes):
    source_fh[16], dest_fh[16], session_id u64, state u8
      state: 0=intent, 1=in_flight, 2=commit_pending

End of records is marked by tag=0 (or EOF).

client_a_ops.log / client_b_ops.log
-----------------------------------
Header (40 bytes):
- magic[8]           = "NFSRCLI\0"
- version u32        = 1
- pad u32            = 0
- client_id[16]
- open_owner_seq_start u64

Record header: 3 bytes (tag u8, length u16), same shape as server log.

Record body (by tag):
- 0x11 OPEN (36 bytes):
    open_owner_seq u64, fh[16], mode u32, ts_ms u64
- 0x12 DELEGATION_HELD (33 bytes):
    stateid_seq u64, fh[16], type u8 (0=read, 1=write), boot_epoch u64
- 0x13 RENAME (49 bytes):
    src_fh[16], dst_fh[16], stateid_seq u64, ts_ms u64, delegation_backed u8
- 0x14 COPY_ISSUE (56 bytes):
    source_fh[16], dest_fh[16], session_id u64, offset u64, len u64
- 0x15 SEQ_TICK (8 bytes):
    new_seq u64

End marked by tag=0 or EOF.

copy_intent.rec
---------------
Single record:
- magic[8]           = "NFSRCPY\0"
- version u32
- pad u32            = 0
- source_fh[16]
- dest_fh[16]
- session_id u64
- total_bytes u64
- bytes_flushed u64
- write_verifier[8]
- committed_flag u8
- pad[7]
- issue_ts_ms u64

namespace.snap
--------------
Textual (UTF-8). One line per entry: `<32-char lowercase hex fh> <absolute-path>`

crc32
-----
The bundled `lib/crc32.c` implements the standard IEEE polynomial
(0xEDB88320, reflected). The rig uses it to check log integrity in some
tooling; it is not used inside individual record bodies.

Reference reconciler bookkeeping
--------------------------------
A conforming reconciler streams each journal once and keeps a small
per-episode summary. The suggested bookkeeping vocabulary — used by
both the reconciler entry point at `tools/reconcile.c` and the reference reader in
`lib/journal_reader.c` — is:

- `seals`      list of parsed `COMMIT_SEAL` records
- `nsops`      list of parsed `NAMESPACE_OP` records
- `is_write`   boolean flag on each parsed reclaim record, true for
               `RECLAIM_DELEG_WRITE` and false for `RECLAIM_DELEG_READ`
- `max_seq`    the highest `stateid_seq` observed across all records
               of a journal (server or client)

These labels are not part of the output contract — they are the
recommended internal names for the summary structures. Use whatever
naming you prefer in your own reconciler.

Magic bytes as they appear in the binary streams (all 8 bytes long,
trailing NUL is part of the magic):

- server_reclaim.log:  b"NFSRSVR\x00"
- client_*_ops.log:    b"NFSRCLI\x00"
- copy_intent.rec:     b"NFSRCPY\x00"

Build-time artifact
-------------------
At image build time the episode generator writes an auxiliary
`episode_manifest.json` under `data/` recording each episode's focused
file handle. It is a build-time convenience only — a conforming
reconciler MUST derive `focused_fh_hex` from each `copy_intent.rec` and
MUST NOT read `episode_manifest.json`.
