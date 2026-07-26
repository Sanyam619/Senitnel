# KVFS on-disk layout

KVFS stores a fixed 4096-byte block array. Blocks 0 and 1 are redundant volume headers (`kvfs_super_t`). The inode table begins at block 2 and spans four blocks. Each inode is 128 bytes. Mode 0 means unused; mode 1 is a regular file. The `name` field stores an absolute path. `direct[]` lists data block indices.

The allocation map occupies blocks 6–7 as a bit vector indexed by block number.

The circular redo area occupies blocks 8–27. Records are byte-aligned streams of `uint8 tag`, `uint16 body_len`, then `body_len` payload bytes. Scan stops at tag 0x00.

Record types:

- 0xA1 TX_OPEN — `uint64 tx_id`, `uint16 patch_count` (informational only)
- 0xA2 BLK_PATCH — `uint32 dst_blk`, then up to 4088 data bytes
- 0xA3 TX_SEAL — `uint64 tx_id`
- 0xA4 BLK_FORGET — `uint64 tx_id`, `uint16 n`, then `n` × `uint32` block indices

Unclean shutdown may leave redundant headers, inode payloads, and allocation maps inconsistent with redo records at the tail of the image.

## Durable recovery contract (post KVFS-441)

These rules define the durable view the site accepts. Older mid-incident tooling still disagrees; do not treat parser acceptance of alternate policy spellings as approval of those spellings.

### Headers

Only headers with valid magic, a CRC covering the first 68 bytes, and `primary_ok == 1` compete. Prefer the greater `epoch`; break ties with the greater `durable_tx`. A non-primary header never wins, even with a larger epoch or durable watermark.

### Durable redo

A transaction is durable only when a matching TX_SEAL exists. Replay durable work in ascending `tx_id` order. Journal append order is not authoritative. Open transactions without a seal leave no durable effect.

The chosen header's `durable_tx` field may lag the highest sealed id present in the redo area. Sealed work beyond that watermark remains durable and must be applied.

`TX_OPEN`'s `patch_count` field is informational. It must not truncate which sealed `BLK_PATCH` records apply.

### Forget

A sealed `BLK_FORGET` suppresses earlier sealed patches to the named blocks when the forget `tx_id` is greater. An unsealed forget record has no effect.

### Patches and map

Partial patch payloads occupy the start of the destination block; remaining bytes in the 4096-byte block are zero. After replay, rebuild the allocation map at blocks 6–7: mark blocks 0–27 used, plus every live inode `direct[]` block. Report the full 8192-byte map as lowercase hex (16384 characters). Redundant superblocks and the raw journal region in rebuilt images match the crash copy.
