A storage cutover left incremental btrfs send parents pointing at the wrong snapshot lineage. Live state under /etc/btrfs/ and /var/lib/btrfs/ drifted from sealed authority; qgroup leases under /var/run/btrfs/ may be torn. Lane streams under /output/lanes/ are wrong or empty, and /output/send-report.json is missing or inconsistent. Surface /app/bin/healthb may report OK while receive stalls and quota over-admits.

Operator cutover starts at /app/ops/run_cutover.sh. Docs under /app/docs/ describe normal layout. Prebuilt binaries live under /app/bin/ (restore copies under /usr/lib/btrfs/bin/ if needed).

Bring the pool back so each lane listed in /etc/btrfs/lane.roster materializes a correct stream.bin under /output/lanes/<name>/ and a coherent /output/send-report.json. The report is JSON with seal_gen equal to the active seal value under /etc/btrfs/pool.seal and a lanes array; each entry includes name, parent_uuid, snap_uuid, origin_kind, and order_index. Only roster lanes may appear under /output/lanes/ or in the report.

origin_kind is incr or base. Preference drop-ins under /etc/btrfs/pref.d/ select the active qgroup inherit mode by folding all drop-ins in lexical order (later files override earlier keys). With equality-inclusive mode, a tip whose epoch is at least its floor materializes incremental stream bytes and reports origin_kind incr; otherwise it materializes base origin bytes and reports origin_kind base. The active mode must be equality-inclusive.

The sealed send journal under /var/lib/btrfs/journal/ is fenced by the active seal generation: tips beyond the seal must not drive runtime parents. Off-roster journal tips must not appear in streams, the report, or the tip map.

An ops journal under /var/lib/btrfs/ops/ records abort and maintenance cutover rows. The sealed maintenance cutover for the active generation target must determine attach lineage and hold; later abort/rollback rows must not leave decoy lineage armed. Attach intent under /var/lib/btrfs/meta/attach.intent must be the raw token seal when cutover succeeds.

Shelves under /var/lib/btrfs/origins/ must stay byte-identical. Cutover must leave no lease marker files under /var/lib/btrfs/origins/ and no torn lease files under /var/run/btrfs/. Host-side marker files under /var/lib/btrfs/volumes/*/host/ must be absent after cutover while sealed volume content stays seated at the attach point. Lease and host scrub only stick when live generation matches the target generation.

Each cutover pass rematerializes a crash tip-map snapshot unless the sealed journal parents are rewritten for the roster. Stale parent UUIDs from the crash must not stay in /var/lib/btrfs/meta/parents.toml.

Volume attach for each roster lane is a flat file /var/lib/btrfs/attach/<lane>.bin that shares an inode with the sealed shelf (same-device hardlink identity), not a decoy byte duplicate and not a nested payload path. After desk refresh, that hardlink identity must still hold.

Two sequential cutover runs, and two concurrent cutover jobs on the same roster, must leave matching streams and clean lease state under /var/run/btrfs/ and /var/lib/btrfs/origins/.
