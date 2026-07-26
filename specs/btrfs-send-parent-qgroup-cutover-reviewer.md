### Decision
GO — Attempt 1. Same decision line as authoring spec.

### Metadata
- Task name: btrfs-send-parent-qgroup-cutover
- Title: Btrfs Send Parent Cutover
- Category: system-administration
- Languages: ["rust", "go", "c"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["btrfs-send", "qgroup", "ops-journal", "leases", "parent-uuid"]
- Milestones: 0

### Discovery budget
- Discovery: Seal generation cap filters journal rows; beyond-seal tips must not win parent map
  Planned location: ops/go/knit_p + data/btrfs/journal/send.wal + etc/btrfs/pool.seal
  Why instruction must not reveal it: Naming the cap filter collapses journal diagnosis to a one-line patch.
- Discovery: Drop-in lexical fold last-wins selects equality-inclusive over earlier strict-gt bait
  Planned location: ops/go/fold_q + etc/btrfs/pref.d/*
  Why instruction must not reveal it: Publishing fold order turns preference into transcription.
- Discovery: Hold rematerialize must clear host markers and torn leases; copy-only fails dual residency
  Planned location: ops/c/hold_c.c + volumes/*/host
  Why instruction must not reveal it: Naming the helper turns the miss into a checklist item.
- Discovery: Attach must hardlink sealed shelf (same inode), not copy decoy bytes
  Planned location: ops/c/link_v.c + volumes/*/sealed vs decoy
  Why instruction must not reveal it: Stating hardlink recipe removes residual attach reasoning.

### Anti-trivialization verdict
Checks 1–21 PASS for symptoms-only sysadmin cutover with ≥3 discoveries, ≥3 topologies, coupled loci, no policy-knob checklist, no three-stub frontier.

### Topology enumeration (3 candidate fix topologies)
1. Ops-helper mesh: knit_p + fold_q + hold_c + link_v coordinate; no single helper greens tip-map, mode, leases, and inode.
2. Journal-authority first: seal/roster fold then preference then attach; skipping tip rewrite fails w9; skipping attach fails i8.
3. Rematerialize-first: hold_c/link_v before fold still fails report/parent tests until knit_p/fold_q/slot_w agree.

### Rubric axes
- Verifiable: PASS — deterministic pytest on streams/tip-map/inodes
- Well-specified: PASS — report schema and outcomes in instruction
- Solvable: PASS — expert ops path via helpers + prebuilt bops
- Difficult: PASS — coupled journal×pref×hold×attach
- Interesting: PASS — real cutover/send-parent work
- Outcome-verified: PASS — grade live state and streams

### Instruction completeness test
Symptoms-only with fair tip-map rewrite, dual residency, hardlink, and equality-inclusive outcomes stated as scenarios.

### Attack path
Agent reads docs, diffs helpers, rewrites Go/C fold/attach logic, re-runs cutover until tip-map/streams/inodes match.

### Smallest plausible patch
Rewrite five helpers (~80–120 LOC total); cannot collapse to one file.

### Collapse audit
PASS — residual hardness in authority coupling; not checklist transcription.
