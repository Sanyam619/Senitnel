### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: speech-diarization-der-calibration-desk
- Title: Speech Diarization DER Desk
- Category: machine-learning
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["diarization", "der", "jer", "clustering-tip", "tip-epoch", "inference-eval"]
- Milestones: 0

### Discovery budget
- Discovery: sealed-max non-retired embed tip is tip_e7 epoch 5 (tip_e9 retired; tip_live unsealed)
  Planned location: data/embed_registry/
  Why instruction must not reveal it: naming the tip id collapses tip_epoch seating
- Discovery: durable clustering method tip is tip_m7 → ahc (live spectral is decoy; tip_m9 retired)
  Planned location: data/cluster_registry/
  Why instruction must not reveal it: naming ahc as the answer collapses clustering cells
- Discovery: DER/JER columns are keyed method_e{epoch}; oracle-count columns green diarprobe but miss bands
  Planned location: data/audio/*.json + tools/diarprobe
  Why instruction must not reveal it: pasting the column key recipe collapses metric seating
- Discovery: trial_pref serving + tip_bind.accept key=value must match both registries or build.rs rematerializes
  Planned location: calib/ + eng/build.rs
  Why instruction must not reveal it: documenting exact receipt keys as a fix checklist collapses SoftHSM gate (outcomes named; exact tokens discovered)

### Anti-trivialization verdict
Hardness axes and discovery/topology checks pass under SoftHSM rematerialize × dual tip × method×epoch metrics. Orthogonal stub flips blocked by rebuild authority.

### Topology enumeration (3 candidate fix topologies)
1. Prefer×bind + five seating modules (realized)
2. Dual crate rematerialize (core/rank) with bind.accept desk_pass
3. Drop-in method roster + embed tip without rematerialize (rejected — TRIVIAL class)

### Rubric axes
Verifiable/well-specified/solvable/difficult/interesting/outcome-verified: Pass for ML diarization eval seating.
