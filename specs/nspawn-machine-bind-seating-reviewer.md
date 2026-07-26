### Decision
GO — Attempt 1. Same decision line as authoring spec: hard sysadmin nspawn bind seating with tip × inode × fold × gen × abort coupling; no debug frontier.

### Metadata
- Task name: nspawn-machine-bind-seating
- Title: Nspawn Bind Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["nspawn", "machine-seating", "bind-attach", "image-tip", "generation-gate", "ops-journal"]
- Milestones: 0

### Discovery budget
- Discovery: Sealed journal cutover for gen.target supplies authoritative tip generations; stale tip_*.gen and live floors are decoys.
  Planned location: `/var/lib/machines/ops/journal.jsonl` + `axle_k.sh` body
  Why instruction must not reveal it: Naming the sealed-tip recipe collapses generation authority to transcription.
- Discovery: Bind= paths that string-match sealed volume objects still fail unless same inode (hardlink); cp creates distinct inodes.
  Planned location: `knit_v.sh` + sealed volumes under `/var/lib/machines/volumes/`
  Why instruction must not reveal it: Stating "use hardlink" turns the novel polarity into a one-line recipe.
- Discovery: abort.d rematerializes broken Bind=/abort into live drop-ins every pass unless cutover.ok matches gen.target with mode=seal; deleting 90-local is wrong.
  Planned location: `helm_w.sh` + abort package vs site_standard
  Why instruction must not reveal it: Pasting the receipt template next to helpers collapses abort coupling.

### Anti-trivialization verdict
All 21 checks PASS for this seating shape: multi-authority coupling, symptoms-only instruction, ≥3 discoveries, ≥3 topologies, not policy-knob transcription, not three-stub polarity alone (inode + tip + fold + abort + ports interact).

### Topology enumeration (3 candidate fix topologies)
1. Ops-helper rewrite: axle_k + knit_v + mesh_p + helm_w + emit_q (+ skim_z) — no single helper greens tip, inode, fold, and seat_ok.
2. Live-state reconcile only: rewrite units/roots/binds by hand without helpers — verifier wipe-and-reseat re-runs broken helpers and rematerialize undoes naive edits.
3. Prefer durable cutover first then fold/attach: receipt + site-standard live drop-in + tip apply + inode attach + emit — skipping inode or tip still fails matrix cells.

### Rubric axes
- Verifiable: PASS — deterministic JSON + inode/gen assertions
- Well-specified: PASS — schema and activity outcomes in instruction/docs
- Solvable: PASS — expert sysadmin hours, bash oracle
- Difficult: PASS — coupled authorities beyond training checklist
- Interesting: PASS — real nspawn seating drift
- Outcome-verified: PASS — grades `/output` + live `/etc`/`/var` state

### Instruction completeness test
PASS — expert can verify schema_tag, machines/ports fields, seat_ok, idempotence, frozen images, and activity rules from instruction + docs without being told which helper to patch.

### Attack path
Agent may green machinectl-health and hand-write JSON; wipe-and-reseat plus inode/tip/fold tests reject that. Smallest plausible patch still spans ≥4 helpers plus receipt.

### Smallest plausible patch
Rewrite axle_k (durable floors + sealed tips), knit_v (hardlink attach), mesh_p (last-wins), helm_w (receipt gate), emit_q (durable roots + seat_ok), skim_z (durable ports), write cutover.ok + site-standard 90-local.

### Collapse audit
PASS — residual hardness is tip×inode×fold×abort×ports; not greppable three stubs alone; instruction not answer key.
