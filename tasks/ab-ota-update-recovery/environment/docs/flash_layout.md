# Flash image layout

Images are a fixed 4096-byte sector array (64 sectors). Sectors 0 and 1 are redundant metadata mirrors for copy A; sectors 2 and 3 mirror copy B. Each metadata sector begins with a 128-byte `slot_hdr_t`. Sectors 4 and 5 duplicate a 128-byte `boot_ldr_t` control record.

Copy A payload occupies sectors 6–21; copy B payload occupies sectors 22–37. Each payload sector is 4096 bytes. Digest chains for each copy begin at sector 38 (copy A) and 42 (copy B): interior nodes are 32-byte SHA-256 values stored sequentially (15 nodes for sixteen payload sectors). The metadata `root_hash` must equal the final rolling digest.

Phase bytes: 0 empty, 1 live, 2 staging, 3 retired. Unclean power loss may leave redundant metadata torn, digest nodes partially updated, or the control record pointing at an integrity-failing copy.
