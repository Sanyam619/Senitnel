### Decision
GO — Attempt 1. Java cold-chain recall holdback with three distributed fix loci; 47 environment files; Step 2b gates green.

### Metadata
- Task name: food-recall-cold-chain-holdback
- Title: Food Recall Cold-Chain Holdback
- Category: security
- Languages: ["java", "bash"]
- Difficulty: hard
- Codebase size: small
- Milestones: 0

### Discovery budget
- Discovery: Signoff clearance is inverted in `PhaseK.tune_a` before grant precedence is evaluated.
  Planned location: `mod-p3/src/main/java/com/distro/engine/p3/PhaseK.java`
  Why instruction must not reveal it: Would collapse precedence diagnosis to a single grep target.
- Discovery: Probe window floor adds 50 to hook timestamp in `ScanC.shift_x`.
  Planned location: `mod-m7/src/main/java/com/distro/ingest/m7/ScanC.java`
  Why instruction must not reveal it: Instruction only states blocked frozen units, not window math.
- Discovery: Dock split propagation returns only first child via `Step2.pick_one`.
  Planned location: `mod-k9/src/main/java/com/distro/core/k9/Step2.java`
  Why instruction must not reveal it: Symptom mentions sibling exposure without naming rebinding helper.

### Collapse audit
Stage: post-Step-2b

Smallest plausible successful patch: Coordinated edits to merge precedence, probe floor, and split propagation helpers across three Maven modules, then offline jar rebuild.

Likely editable frontier: mod-p3/PhaseK.java, mod-m7/ScanC.java, mod-k9/Step2.java

Collapse verdict: PASS (WARN on RC2 predictability and GX3 borderline edit distance)

### Per-test feasibility pre-check
- test_k9_active_notice_blocks: ACTIVE dairy unit HELD — LOW
- test_m4_unrelated_release: frozen unit RELEASED with valid probe window — LOW
- test_p2_cleared_excursion: cleared review releases — LOW
- test_q7_split_lineage: both split children HELD — LOW
- test_s3_rerun_stable: byte-identical reruns — LOW
- test_w2_hidden_day: cross-store recall containment on day_r0416 — LOW
