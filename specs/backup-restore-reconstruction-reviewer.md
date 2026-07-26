### Decision
GO — current sysadmin fleet-recovery design.

### Metadata
- Task name: backup-restore-reconstruction
- Title: Backup Restore Reconstruction
- Category: system-administration
- Languages: ["bash", "rust"]
- Difficulty: hard
- Codebase size: small
- Tags: ["fleet-ops", "volume-attach", "ops-journal", "leases", "dropin-policy", "cutover-receipt"]
- Milestones: 0

### Graded work
The agent repairs the live operator recovery path (shell helpers + drop-ins +
journal cutover) so `/app/ops/run_recovery.sh` can reconcile fleet state and
publish the report. Prebuilt `fleetctl` / `yarder` / `fleetpeek` are not
source-edit targets. Acceptance turns on:

- lexical fold of `/etc/fleet/reconcile.d/*.conf` into canonical effective policy;
- target-generation `mode=seal` journal cutover over later rollback;
- durable `cutover.ok` that stops abort-window synonym rematerialize;
- `gen.live == gen.target`, `attach.intent=seal`, `PAYLOAD_LINEAGE=sealed`;
- complete live lease bags and exact quarantine gate presence;
- same-inode sealed runtime attaches with cutover hold tokens;
- five-episode `/output/reconciliation.json`, restored trees, and `run.stamp`.

This is not a lab-pool / byte-span / Rust-module / `repair.json` task.

### Difficulty
Multiple live authorities undo partial repairs: journal selection drives
generation/hold/intent/lineage; fold rematerializes synonym abort drop-ins
without a matching cutover receipt; generation gates leases and gates; fleetd
copy-rematerializes when lineage or holds disagree with sealed attaches. The
alpha–epsilon matrix stresses roster fencing, sealed-vs-newer borrow, decoy
payload, fragment order, and quarantine interaction.

### Solution
Align the live `90-local` drop-in with site standard. Repair `axle_p` to apply
the sealed target-gen cutover and write `cutover.ok`, `attach.intent=seal`, and
`PAYLOAD_LINEAGE=sealed`. Repair `fold_d` so abort residue applies only without
a matching receipt. Repair `weave_k` to fold drop-ins and preserve axle-armed
env. Repair `pull_m` / `mark_t` for full leases and exact gates after gen
alignment. Repair `bind_v` for sealed hardlinks + holds. Run
`/app/ops/run_recovery.sh`.

### Verification
`tests/test.sh` runs pytest from `/tests` and sets reward from CTRF pass count
(full suite), not from an empty/no-op runner exit alone. The fixture deletes
`/output`, restores image bins if needed, runs recovery twice for identical
trees, and independently derives episode outcomes plus live admin invariants
(fold, cutover receipt, gen/intent/lineage/hold, leases, gates, inodes,
fleetd, stamp, immutability).

### Anti-cheating
Handwritten `/output` is deleted before verification. Re-entry runs the real
recovery path twice. Mutating `/app/data`, replacing fleetpeek, copying sealed
bytes instead of attaching the sealed inode, or skipping helpers cannot clear
the suite.

### Collapse audit
Smallest successful repair covers drop-in state plus coupled helpers across
`/app/ops`, `/app/bag`, `/app/rim`, and `/app/deck`. Instruction stays
symptoms-only; exact outcomes live under `/app/docs/`.
