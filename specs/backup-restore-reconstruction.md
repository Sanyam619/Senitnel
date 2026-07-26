### Decision
GO — hard single-step system-administration task. This specification replaces
the retired lab/object-pool/snapshot-span design.

### Metadata
- version: 2
- Task name: backup-restore-reconstruction
- Title: Backup Restore Reconstruction
- Category: system-administration
- Languages: ["bash", "rust"]
- Difficulty: hard
- Codebase size: small
- Tags: ["fleet-ops", "volume-attach", "ops-journal", "leases", "dropin-policy"]
- Milestones: 0

## Authoring Brief

### Public contract
Five alpha–epsilon crash-export episodes did not complete recovery. Surface
health may remain green while live policy, journal generation, leases,
quarantine gates, and runtime payload attaches disagree. The agent must repair
the live shell-admin path and run `/app/ops/run_recovery.sh` so it writes:

- `/output/reconciliation.json`, with each episode carrying `roster_final`,
  `borrow_peer`, `payload_digest`, `fragment_digest`, and `decision`;
- `/output/restored/<episode>/{payload.bin,fragments.bin,report.json}`;
- `/output/meta/run.stamp`.

Crash-export data and the pinned inspector remain immutable.

### Failure topology
The task couples live admin authorities (not lab-pool/span/Rust repair):

1. `/etc/fleet/reconcile.d/*.conf` folds lexically into effective policy.
2. The target-generation `mode=seal` journal cutover outranks a later
   provisional rollback.
3. Abort-window drop-ins rematerialize unless durable `cutover.ok` matches.
4. `gen.live` aligns with `gen.target`; `attach.intent=seal`;
   `PAYLOAD_LINEAGE=sealed` (volume directory, not the mode token).
5. Full lease bags drive live/clear, sealed-first, earliest-ts borrow choice.
6. Quarantine is exact per-episode gate-file presence; runtime payloads share
   the sealed payload inode and carry the cutover hold.

Fleetd rematerialization couples lineage, holds, and inode identity, so a
partial or incorrectly ordered repair does not remain valid.

### Environment shape
- Correct prebuilt Rust binaries under `/app/bin`, with restore copies under
  `/usr/lib/fleet/bin`.
- Broken live shell helpers under `/app/ops`, `/app/bag`, `/app/rim`, and
  `/app/deck`.
- Live host state under `/etc/fleet`, `/var/lib/fleet`, and `/var/run/fleet`.
- Immutable episode exports under `/app/data/episodes`.
- Solver-visible operational contracts under `/app/docs`.

### Test plan
- Require all five report rows and exact independently derived values.
- Require restored payload, fragment, and local reports to match aggregate
  digests and decisions.
- Exercise alpha post-seal roster filtering.
- Exercise beta sealed-vs-newer borrow and full claim preservation.
- Exercise gamma sealed inode attach versus decoy/copy.
- Exercise delta seal-ordinal fragment ordering.
- Exercise epsilon policy plus quarantine borrow behavior.
- Verify lexical drop-in fold and canonical run stamp.
- Verify journal target generation, exact raw `seal` attach intent, and hold.
- Verify complete lease sets, fleetd pidfile, data immutability, and inspector
  digest.
- Run recovery twice and require deterministic output.

### Drafting guardrails
- Keep `instruction.md` symptoms-only.
- Document graded outcomes and exact raw-token distinctions in `/app/docs`;
  do not publish a numbered fix recipe.
- Do not turn the task back into Rust source debugging.
- Do not use privileged mounts; same-inode hardlinks are the attach primitive.
- Do not reduce the frontier to independent synonym/boolean flips.

### Triviality ledger
- Editing only the effective config fails because tests recompute the drop-in
  fold and journal/generation remain wrong.
- Taking the last journal row fails because the target-generation sealed
  cutover is authoritative.
- Aligning generation alone fails because broken lease and gate helpers still
  flatten/invert state.
- Copying correct bytes fails inode checks.
- Hardlinking before correct hold/lineage state can be undone by fleetd.
- Handwriting `/output` fails because the verifier deletes it and re-enters
  recovery twice.

### Per-gate pitfall inventory
- Instruction sufficiency: explicitly document `attach.intent` raw token
  `seal`, not the adjective “sealed”.
- Category: grade live `/etc`/`/var` administration through shell helpers and
  a prebuilt binary, not Rust rewrites.
- Collapse: preserve journal→generation→lease/gate→hold/attach coupling.
- Packaging: include `environment/.dockerignore`; exclude authoring rubric,
  explanation, validation, and construction files.
- Verifier: derive expected outcomes independently; do not expose golden
  output artifacts in the image.

### Construction manifest summary
Oracle-touched locations:

- `ops/weave_k.sh` — lexical drop-in fold and fleetd environment;
- `ops/axle_p.sh` — sealed journal cutover, generation, intent, hold;
- `bag/pull_m.sh` — generation-gated complete lease installation;
- `rim/mark_t.sh` — generation-gated quarantine gate materialization;
- `deck/bind_v.sh` — same-inode sealed attach and runtime hold;
- `config/reconcile.d/90-local.conf` — final canonical live override.

The verifier distributes checks across policy, journal/generation, leases,
gates, attaches, per-episode reconciliation, and immutable artifacts. No
single location controls a majority.
