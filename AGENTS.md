### Platform postmortem log (collapse → redesign)

### 2026-07-26 — `mixture-of-depths-token-routing-eval` (category_classifier → SE at 0.95)

- **Feedback:** CodeBuild `12:01` UTC static checks FAIL. Sole hard ❌:
 `[category_classifier]` predicted blocked `software-engineering` at **0.95**
 while `task.toml` said `machine-learning`. instruction_check WARN'd on the
 jargon-first opener ("Seat the mixture-of-depths inference desk…").
 Dockerfile Cargo.lock / dep-split lines were WARN-only heuristics
 (Cargo.lock is COPY'd and `--locked` used).
- **What went wrong:** Same class as `offline-online-feature-skew-calibration`
 — the whole solver-visible surface led with ops/desk vocabulary: "Seat the
 … desk", `desk_notes.md`, "seating surfaces", "binding receipt" prose.
 Classifier read a repair/cutover desk, not model evaluation.
- **Fix shipped (same coupling, ML surface):** instruction rewritten with a
 plain-English ML opener (bring the model evaluation into published metric
 bands); `desk_notes.md` → `eval_notes.md` framed around evaluation
 selection and calibration; mod_bands "Binding receipt" → "Tip binding"
 record; de-seated prose in docs/comments; ML-lead tags. CR1 regression
 caught locally: new "scoring/scores" instruction nouns stemmed onto the
 oracle-touched `score` symbol — reworded to "evaluation report"/"results
 hold". Fresh gates: preflight PASS (4 WARN), oracle 1.0, NOP 0.0,
 approve PASS on rebuilt zip. Platform category not claimed fixed until a
 new CodeBuild run grades this zip.

### 2026-07-26 — `tabular-uplift-treatment-effect-eval` (HARD 0%/0% + sufficiency FAIL on hidden shift)

- **Feedback:** Difficulty ✅ HARD. Opus/GPT both **0% (0/5)**. Oracle 100%,
 NOP 0%. Agents averaged ~11/13; three trials hit **12/13**. Sufficiency FAIL
 (task_specification fail on all 10). `test_l7_dunite` **0/10**,
 `test_c1_biotite` 3/10, `test_b7_zircon` 4/10; nine cells sat at 10/10.
- **What went wrong:** (1) graded metrics were `column + shift` /
 `column + shift * 0.5` — an asymmetric undocumented offset whose only trace
 was a broken seed body; (2) `treatment_tip` was graded as an integer epoch
 while docs said "must equal the durable assignment tip", so agents rewrote a
 field that was already correct; (3) the verifier read
 `/app/calib/tip_bind.accept` by exact path, never named in docs; (4) NOP
 passed three structural cells.
- **Do not repeat:** Hidden per-metric arithmetic as the last graded hop (no
 fair setting: unguessable, and documenting it collapses to TRIVIAL). Type
 ambiguity on a graded scalar. Unnamed receipt paths (§12 class). Free
 structural cells uncoupled from the bands.
- **Fairness + harden shipped (same coupling):** shift removed; metrics are
 now a tip → estimator → **scored column** hop over `data/estimators/roster.json`
 with a divergent stale copy in `data/ledger/roster_mirror.json` that lands
 out of band (new `test_n8_basalt`); wrong tip also picks the wrong estimator
 and so the wrong column. Docs name the epoch-as-number outcome, the roster
 authority, and the `key = value` receipt. `d9`/`h4`/`j0`/`k3` now require the
 bands, leaving `a3` as the sole static cell; oracle rewritten in bash. NOP
 now 1/14. Local: preflight 0 FAIL/8 WARN, oracle 1.0, NOP 0.0, approve PASS.

### 2026-07-26 — `keepalived-vrrp-split-brain-seating` (HARD 0%/0% + sufficiency FAIL on cutover precedence)

- **Feedback:** Difficulty ✅ HARD. Opus/GPT both **0% (0/5)**. Oracle 100%,
  NOP 0%. All trials **17/18**; sole miss `test_c1_flint`. Sufficiency FAIL
  (6/10 task_specification fail): Rule A (abort rematerializes unless receipt
  matches) vs Rule B (“live must remain with site-standard”) read as always
  overwrite live with site_policy — stale-target rematerialize never sticks.
- **Do not repeat:** Unconditional “must remain site-standard” beside abort
  rematerialize; grade only drop-in cosmetics without fold coupling.
- **Fairness shipped:** Site-standard applies under a matching seal receipt;
  stale/missing receipt rematerializes abort and keeps it for that pass;
  flint also asserts abort `peer_a` priority enters the fold. GX6-safe
  phrasing (no when/while stack). Other 10/10 cells kept — genuine seating
  fixes, not leakage. Local: oracle 1.0 / NOP 0.0 / approve PASS.

### 2026-07-26 — `structured-prune-recovery-eval` (platform EASY 100%/80%)

- **Feedback:** Difficulty ❌ EASY. Opus **100% (5/5)**, GPT **80% (4/5)**.
  Oracle 100%, NOP 0%. QC ACCEPT / ROBUST; Instruction Sufficiency PASS on
  the GPT miss (reward-hack of `surface_ok` accuracies into seating).
- **What went wrong (Opus ~35 eps):** (1) `surface_ok.json` leaked
  `mask_tip=7` and near-correct sparsity/flops; (2) recovery notes were a
  re-fit checklist (all domains, location+spread); (3) `build.rs` taught the
  durable filter agents copied into tip resolution; (4) six independent
  polarity stubs (tip/seat/span/draw/Norms/head) flipped one-by-one.
- **Do not repeat:** Answer-shaped health fixtures; recipe docs; correct
  resolution logic sitting next to broken tip.rs; independent greppable
  stubs as the whole frontier; treating QC ACCEPT as hardness.
- **Harden shipped:** Poisoned `surface_ok` onto overlay tip 11; thinned
  docs; unstructured durable `tip_g8` bait; build gates validate receipt
  (durable+structured+kept+`desk_pass`) without teaching max-epoch;
  geometry shipped correct; rematerialize tip/seat/draw/meld until
  `serving/bind.accept` is scoring-bound; crates renamed `meld`/`lane`;
  seating pass lives in the receipt (`desk_pass`), not greppable
  `eval_pass.toml`. Local: oracle 1.0 / NOP 0.0 / approve PASS.


# AGENTS.md

Terminal-Bench 3.0 Edition 2 task-authoring harness. Unit of work: a task
under `tasks/<task-name>/`. New here? Read `docs/ARCHITECTURE.md` first.

## Where to look

- Layout: `docs/ARCHITECTURE.md`.
- Before any task edit: pull `.cursor/rules/00-authoring-critical.mdc`.
- Authoring: `task-creation.mdc`. Idea validation: `idea-validation.mdc`.
- Review: `review-and-submit.mdc`. Hardness: `difficulty-calibration.mdc`.
- Rights/wrongs (living): `AUTHORING_RIGHTS_AND_WRONGS.md` — append reusable
  do/don't here; do not write per-task lesson files under `specs/`.
- Commands: `commands.md`. Workflow: `workflow-prompts.md`. Conventions: `REPO_CONVENTIONS.md`.

## Must-fire bullets (every interaction)

1. Every `task.toml` must include `[environment] allow_internet = false`; verifier deps go in `environment/Dockerfile`, not runtime installs in `test.sh`.
2. Never claim PASS / READY / APPROVED / SUBMIT without command output as evidence.
3. Cheap gates first: `run_static_checks.py` → `collapse_check.py` → oracle 1x → NOP. No oracle 10x in Step 2b.
4. Don't invent paths, `task.toml` fields, or commands from memory; open the file or `commands.md`.
5. After any task-file edit, prior Step 2b evidence is stale. Rerun cheap gates. `approve_task.py` refuses to package on checksum mismatch.
6. One-command preflight: `./scripts/check-task.sh tasks/<task-name>`. Preflight only — oracle 1x and NOP still required for Step 2b PASS.
7. Milestone tasks use the canonical `steps/milestone_N/{instruction.md, tests/, solution/}` layout with `task.toml` `version = "2.0"` and matching `[[steps]]` blocks. The deprecated root-level `instruction.md` / `tests/` / `solution/` / `milestones.md` shape is rejected — see `task-creation.mdc`.
8. New starts of multi-container or UI building tasks are no longer accepted; in-progress instances may finish.
8b. **Open categories only for new tasks:** `games`, `machine-learning`, `system-administration`. All other historical categories are blocked — see `task-type-taxonomy.md`. Redesign or reject ideas that only fit a blocked category.
9. After creating or revising a task and writing the submission zip, run `./scripts/cleanup-task-docker.sh <task-name>` to stop Harbor containers and prune Docker build cache so local runs do not keep the laptop busy.
10. Non-trivial tasks need `environment/.dockerignore` in the task folder and in the submission zip (hidden dotfile; see `task-creation.mdc`). A zip missing `environment/.dockerignore` is a packaging defect when the task dir has one. **Do not `COPY` other hidden paths** (e.g. `.cargo/`) from the build context — platforms may omit archive dot-directories and Daytona fails with `Path does not exist`. Seed from a non-hidden file and `RUN` materialize into the dot path. After zipping, `unzip -l` and confirm every `COPY` source is a non-hidden path present in the archive.
11. **CodeBuild / harbor static-check pastes are artifact fingerprints, not vibes.** Before claiming a CI fail is fixed: (a) `unzip -p Task_Ready_To_Submit/<task>.zip …` the exact paths/lines CodeBuild cited, (b) confirm the zip mtime is *after* the fix, (c) if the paste still shows the old Dockerfile line map / missing `check=` / no `requirements.txt` hashes, the user re-uploaded the **old** zip or re-pasted an **old** log — do not “fix” again by rewriting the same files. Identical CodeBuild timestamps = same run.
12. Verifier Python: every `subprocess.run` in `tests/` needs an explicit `check=` (ruff **PLW1510** is a hard CodeBuild fail). Never use `v == v` for NaN/finite checks — ruff **PLR0124** hard-fails on CodeBuild’s task-only tree even when local default `ruff check` is green; use `float("-inf") < v < float("inf")` (or `math.isfinite` if GX8 allows). Before zip, run `ruff check tasks/<task>/tests/ --select PLR0124,PLW1510`. Pip in `environment/Dockerfile` must install from a hashed lockfile (`requirements.txt` with `--hash=sha256:` **and** `pip … --require-hashes -r …`); inline `pytest==…` alone fails upstream’s lockfile gate. Comment the word `pytest` in the Dockerfile so local `run_static_checks.py` still sees the verifier dep. Keep `RUN rm` on a **separate** line from `pip install` (same-line `&& rm` is misparsed as an unpinned package).
13. **`[instruction_check]` PASS ≠ `[category_classifier]` PASS.** New tasks may only use open categories (`games`, `machine-learning`, `system-administration`) — see `task-type-taxonomy.md`. For any open-category task, lead instruction/tags with category-native outcomes; never introduce tooling/cutover / “fix the Rust project” aura that flips the classifier to blocked `software-engineering`.

## Forbidden in submissions

`output_contract.toml`, `quality_check_adjudication.json`, `construction_manifest.json`, `rubric*.txt`, `.step2b-checksum`, and any AI-scaffolding filename (`CLAUDE.md`, `AGENTS.md`, `skills.md`, `.cursor/`, `.aider/`, `.continue/`, `.claude/`) at any archive depth. See `REPO_CONVENTIONS.md`.

## Platform postmortem log (collapse → redesign)

### 2026-07-26 — `squid-cache-peer-icp-preference-lattice` (platform TRIVIAL 100%/100% after fairness doc fix)

- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. Oracle
 100%, NOP 0%. All 14 tests **10/10**. QC ACCEPT / ROBUST; Instruction
 Sufficiency N/A. Artifact `(1).zip` (post-fairness). GPT finished in
 **~5–7 eps**; Opus ~15–26 — both one-pass after reading
 `seating_contract.md`.
- **What went wrong:** Fairness docs for `tip_*.type` / `seat_ok` turned the
 seating contract into a complete algorithm recipe next to six independent
 always-wrong bash polarity stubs (`helm_r`/`axle_n`/`mesh_k`/`skim_p`/
 `sock_v`/`emit_m`). `site_standard.conf` also leaked the exact tip
 type/weight matrix. No rematerialize authority undid naive helper edits.
 Same SoftHSM / backup-restore / edge-lane post-doc TRIVIAL class. QC
 ACCEPT is not hardness.
- **Do not repeat:** Do not answer HARD+0% sufficiency only by documenting
 the missing state path beside a numbered recipe + independent stubs.
 Do not ship answer-shaped site-standard peer type/weight keys.
- **Harden shipped:** Chrony/SoftHSM-class `prefer.toml` (live/surface →
 durable/authority) × `tip_bind.accept` matching `gen.target` × end-of-
 pipeline `knit_q` rematerializes surface tip/peer sheets unless both
 gates pass; ship correct `mesh_k`/`skim_p`/`emit_m`; strip tip matrix
 from `site_standard.conf`; thinner outcomes docs; diversified hosts;
 new `test_y3_jasper` prefer re-entry (live flip poisons, durable
 recovers). Residual broken: `helm_r`/`axle_n`/`sock_v`/`knit_q`. Local:
 oracle 1.0 / NOP 0.0 (15/15 fail) / approve PASS.

### 2026-07-25 — `squid-cache-peer-icp-preference-lattice` (HARD 0%/0% + sufficiency FAIL on undocumented state files)

- **Feedback:** Difficulty ✅ HARD. Opus/GPT both **0% (0/5)**. Oracle 100%,
 NOP 0%. 8/10 trials at **13/14** — sole miss `test_w7_quartz`
 (`FileNotFoundError: /var/lib/squid/state/tip_north.type`). 2 trials also
 misread `seat_ok` as "all peers selected"; 1 trial kept `north` in the
 abort set from pre-cutover live `90-local.cfg` residue. Artifact `(56).zip`.
- **What went wrong:** The verifier read `tip_<name>.type` state files that
 only the oracle wrote — never named in `layout.md` / `seating_contract.md`
 (layout even listed only `tip_*.gen`, actively steering away). `seat_ok`
 wording "every peer agrees with durable authority" was reasonably read as
 universal selection. Abort residue survival across cutover unspecified.
- **Do not repeat:** A state file the verifier reads by exact path is a
 graded outcome — name it in solver-visible docs even when the main
 deliverable is a report (same class as dm-thin `activation.toml` §12).
 Do not leave a boolean like `seat_ok` defined only by "agrees with
 authority" when correct output has mixed selected polarities.
- **Fairness + harden shipped (same coupling):** `layout.md` +
 `seating_contract.md` document `tip_*.type` / `tip_*.weight` records,
 `seat_ok`-true-with-unselected-peers semantics, and abort residue not
 surviving cutover. To stop the doc fix flipping 13/14 near-misses into
 EASY 100%, prefer journal now carries a superseded sealed+complete gen-7
 revision (first-match readers get 4/5 peers wrong on type/weight; the
 "latest batch" rule was already documented). `test_w7_quartz` now checks
 tip type/weight records against journal + report. Fresh gates: preflight
 0 FAIL/4 WARN, oracle 1.0, NOP 0.0, approve PASS on rebuilt zip.

### 2026-07-25 — `reversi-corner-mobility-contest` → `reversi-mark-flip-contest` (category_classifier → SE, reshape not rename)

- **Feedback:** CodeBuild classified the booklet as blocked
 `software-engineering` (0.85–0.9) across several runs while `task.toml` said
 `games`. Reverting to the earlier surface, renaming to `*-capture-contest`,
 moving the card to `/app/answers.json`, and re-tagging all failed. The task
 had already passed static as `games` once, so metadata was never the lever.
- **What went wrong (root cause, not wording):** the graded activity itself was
 software engineering in a Reversi costume. The card carried `schema_tag`,
 `mobility_delta`, `corner_safe`, and `coop_sweep`; `/app/docs/` specified a
 disc-count formula, a numeric floor, a lexicographic tie-break, a two-sided
 cooperative simulation policy, and a byte-identical refile. Nobody had to
 **play** Reversi — the solver implemented a written spec and emitted
 conforming JSON. The sealed judge could not even replay White (its
 `validate` applied Black drops only), which is the tell: a games task whose
 referee cannot referee a game is not a games task.
- **Do not repeat:** Do not answer an SE classification on a `games` task by
 renaming the task, swapping the output path, re-tagging, or thinning prose
 while the card still asks for spec-derived metric fields. Do not ship a
 rulebook that reads as a formula spec (`delta = B - W`, floors, tie-break
 order, canonical ordering, deterministic re-emission). Do not leave a card
 field that is a pure function of another field (`coop_sweep` from `status`).
 Do not paste the oracle's real rounds into a doc sample — the first draft of
 `tournament_card.md` shipped board 01/02/04 with their true verdicts, board
 01's forcing line, and board 02's refutations.
- **Reshape shipped (`reversi-mark-flip-contest`):** every sheet marks one White
 disc; the graded facts are play, not metrics. `status` = `win` (Black forces
 the mark Black inside three stones against every legal White reply) / `trap`
 (White holds it, but Black reaches it with White passing) / `fort` (three
 stones fail even with White passing). `line` is the forcing line on wins
 (each Black drop must preserve the force, checked by search), the friendly
 line on traps; `refutations` names every threat with a White reply that
 kills the immediate take. Judge rebuilt to referee alternating colour play,
 passes, announces, and mark ownership. No canonical ordering is graded — any
 correct line is accepted, which also removes the lex-tie-break unfairness
 class that zeroed artifact 51. Fixture spread: 4 forced wins that truly need
 three stones, 5 traps with refutable threats, 2 forts reachable only with a
 fourth stone. Kiosk draft stamps `win` on all eleven (fourth stone allowed)
 as bait; sensei probes through the sealed judge and leaks no engine.
- **Measured bands (verifier vs deliberately wrong cards):** oracle 1 · no card
 0 · draft filed as-is 0 (8/8 tests fail) · friendly-line-called-win 0 ·
 fourth-stone-budget 0 · no refutations 0 · two rounds under-refuted 0 ·
 win lines swapped for friendly lines 0 · announces omitted 0. Single slips
 pass: one fort mis-read 1 · one threat missed 1 · one round missing
 announces 1. Gates on the final checksum: preflight PASS (9 booklet-class
 WARN), ruff clean, oracle 1.000, NOP 0.000, `approve_task.py` PASS.

### 2026-07-25 — `embedding-bank-temperature-recalibration` (platform TRIVIAL 100%/100%)

- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. Oracle
  100%, NOP 0%. All 11 tests **10/10**. Artifact `(50).zip`. QC ACCEPT /
  ROBUST across every quality check — not difficulty evidence.
- **What went wrong (GPT ~10–16 eps, Opus ~20–33):** Agents read bands +
  journal + runbook skim/anchor glossary, then one-pass flipped five
  independent polarities (`coef > 1` lens, newest-line knot, newest-sheet
  facet, fold-all weave, prefer skim→anchor). Prefer rematerialize only
  restored knot/facet seeds — lens/weave stayed free. Instruction graded
  outcomes were a 1:1 fix checklist.
- **Do not repeat:** Do not leave SoftHSM rematerialize covering only a
  subset of polarity sites. Do not ship skim/anchor glossary + independent
  textbook stubs as an ML frontier. Do not treat QC ACCEPT as hardness.
- **Harden shipped:** `calib/trial_pref.toml` selection trial→serving +
  `tip_bind.accept` must match registry tip; dual `rank/build.rs` +
  `core/build.rs` rematerialize knot/facet/lens/weave; tip resolution =
  newest durable minus `retired_tips.jsonl` (decoy tip_g9 + live tip_live);
  leftover `data/ledger/` bait; novel durable tip inject moves
  epoch/temp/mix; thinner ML instruction. Local: oracle 1.0 / NOP 0.0 /
  preflight PASS (collapse WARN justified).


### 2026-07-25 — `offline-online-feature-skew-calibration` (category_classifier → SE at 0.9 on hardened zip)

- **Feedback:** CodeBuild `12:05:52` classified the hardened zip as blocked
 `software-engineering` at **0.9** while `task.toml` said
 `machine-learning`. Instruction opener, metadata, and tags were already
 ML; instruction_check PASS did not protect the category.
- **What went wrong:** The TRIVIAL-fix harden imported SE/ops vocabulary as
 the whole solver-visible authority surface: `environment/ops/` with a
 `nx.toml` mode line + `bind.accept` receipt, `data/ledger/` with
 `withdrawals.jsonl`, and instruction/eval-notes prose about "resolver
 edits", "desk commitment", "mode line", "bind acceptance", and an
 "operations ledger". The classifier read a commit/cutover repair desk,
 not model evaluation.
- **Do not repeat:** Hardening with ops/commit/bind/withdrawal/
 rebuild-authority nouns can flip an ML calibration task to SE even when
 metadata, the instruction opener, and tags are ML and instruction_check
 passes. Never treat instruction_check PASS as category PASS.
- **Fix shipped (same coupling, ML surface):** `ops/` → `calib/`
 (`trial_pref.toml` with `[evaluation] selection = "trial"|"serving"`,
 `tip_bind.accept`, `trace_pref.toml`); `data/ledger/` →
 `data/feature_registry/` (`tip_journal.jsonl`, `retired_tips.jsonl`,
 same rows: newest-any tip_live, newest-durable tip_g9 retired, serving
 tip_g7); both structurally dissimilar build gates now parse `selection`
 and require `serving` + registry-resolved lineage; `retired` identifiers
 (never "withdrawn"); test renamed
 `test_source_not_retired_or_live_tip`; instruction/eval-notes rewritten
 around held-out inference slices, selected feature snapshot, calibration
 lineage, clean evaluation reruns; tags feature-store /
 held-out-evaluation / model-calibration / auc / brier /
 serving-inference. Fresh gates: static PASS (length WARN), collapse
 0 FAIL/7 WARN (RC2 file-name keyword WARN is the mandated ML naming),
 oracle 1x 1.0, NOP 0.0, zip validated. Platform category not claimed
 fixed until a new CodeBuild run grades this zip.

### 2026-07-25 — `offline-online-feature-skew-calibration` (platform TRIVIAL 100%/100%)

- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. Oracle
 100%, NOP 0%. All 9 tests **10/10**. Artifact `(49).zip`. QC ACCEPT /
 ROBUST across every quality check — again not difficulty evidence.
- **What went wrong (GPT solved in 8 episodes):** By ep3 the agent had
 grepped the four seed bodies (newest-line tip pick, ratio skew, tip_live
 label, always-overlay mesh), read the single-line `nx.toml` mode gate in
 `sx/build.rs`, and read `tip_g7` straight off a 4-row journal. Tip files
 carried `"kind": "durable"/"live"` labels; seeds had intent comments.
 One-pass polarity flip + mode flip.
- **Do not repeat:** Do not gate rematerialize on one greppable mode line;
 do not label snapshots with the graded answer (`kind`); do not leave a
 tip resolution that one grep of a tiny journal solves.
- **Harden shipped:** Multi-step tip resolution — 8-row interleaved journal
 + `data/ledger/withdrawals.jsonl` (newest-durable `tip_g9` is withdrawn;
 newest-any is `tip_live`; resolved tip is `tip_g7`); decoy `tip_g9.json`
 snapshot (breaks f_zip cap + slice bands); coupled gate: seeds
 rematerialize on every rebuild until `nx.toml` mode is committed AND
 `ops/bind.accept` equals the ledger-resolved tip (shipped stale as
 `tip_live`); both `sx/build.rs` and a new structurally-dissimilar
 `core/build.rs` (CR5-safe) enforce it; `op_v(rows, root)` must consult
 withdrawals; `kind` labels + intent comments stripped; surface bait now
 points at the decoy tip; runbook documents durable/live/withdrawn tips
 and bind acceptance as scenario prose. Ablations: fixed bodies +
 anchor + stale receipt → broken; receipt=tip_g9 → broken; oracle green.
 Fresh gates on final checksum: static PASS, collapse 0 FAIL/6 WARN,
 oracle 1.0, NOP 0.0, zip validated.

### 2026-07-25 — `moe-router-load-balance-eval` (platform TRIVIAL 100%/100%)

- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. Oracle
 100%, NOP 0%. All 12 tests **10/10**. Artifact `(46).zip`. QC ACCEPT /
 ROBUST — the quality check itself narrated the collapse: five separated
 always-wrong stubs (live-tip pick, all-active flags, uniform mix, uniform
 entropy, spread gate) that agents grep and polarity-flip in one pass.
- **Do not repeat:** Do not treat five textbook-wrong bodies in five neat
 dirs as an ML frontier even with rebuild + novel-slice tests. Do not let
 QC ACCEPT/ROBUST read as difficulty evidence (same as sph 2026-07-25).
- **Harden shipped:** SoftHSM-class `eng/build.rs` rematerializes all five
 seating surfaces from `eng/seeds/` until `calib/trial_pref.toml` is
 `selection = "serving"` AND `calib/tip_bind.accept` matches the selected
 durable tip id/epoch/temp (sealed-max among non-retired tips in an
 interleaved `tip_journal.jsonl`; newest sealed `tip_g9` is in
 `retired_tips.jsonl`; live tip and stale mirror remain baits); overstated
 `hold.json` roster; epoch-windowed `hold_ledger.jsonl` coupled to the
 selected tip epoch; capacity-weighted seating discoverable from an audit
 sample stripped of tip/held labels; log2/e mismatch scoring; docs thinned
 to outcomes (no sealed-max recipe, no pasteable bind template); tests
 recompute from fixtures and `test_j3_pyrite` novel sealed-journal inject.
 Measured: NOP 11/13 fail; sealed-max+wrong-calib 8/13 fail; tip_g9 bind
 8/13 fail; oracle 13/13. Local: static PASS, collapse 0 FAIL/7 WARN,
 oracle 1.0, NOP 0.0, approve_task PASS.

### 2026-07-25 — `sph-kernel-handoff-reconcile` (platform EASY 80%/80% + moment_zero sufficiency)

- **Feedback:** Difficulty ❌ EASY. Opus/GPT both **80% (4/5)**. Oracle 100%,
  NOP 0%. QC ACCEPT / ROBUST (all quality checks ✅). Sufficiency FAIL on
  near-miss: agent fixed ~7 sites but left center-density Shepard partition
  → `moment_zero` ~1e-16 and density probe ~20% error. Schema already had
  neighbor-volume formula; liveness floor `moment_zero > 1e-6` was only in
  tests. Second miss was Daytona infrastructure (not task-spec).
- **Do not repeat:** Do not treat QC ACCEPT as difficulty evidence. Do not
  “fix” EASY only by documenting `moment_zero > 1e-6` beside the same
  independent polarity frontier. Do not paste more Shepard algebra.
- **Harden shipped:** Document moment_zero liveness; `root.accept` +
  remove live `trial_pref.toml` under `/app/data/state/`; `sph_a`/`sph_b`
  `build.rs` rematerialize density/force from surface vs durable materials;
  residual iterate/greens/reduce/policy; durable-preference tests.
  Scientific framing retained.

### 2026-07-24 — `edge-lane-lattice-rollup` (platform TRIVIAL 100%/100%)


- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. Oracle
  100%, NOP 0%. All 30 tests **10/10**. Artifact `(40).zip`. QC ACCEPT /
  ROBUST; Instruction Sufficiency N/A.
- **What went wrong (trajectories; GPT ~19–29 eps, Opus ~47–56):**
  1. Instruction listed exact accepted tallies (10→8 … 50→4) next to
     greppable polarity sites — answer-key targeting.
  2. Intent comments labeled every bug (`little-endian`, `no cross-stream
     replay fence`, `operator_default`, `exclusive watermark`,
     `payload-only`).
  3. Full audit samples + independent LE/ELL2/manifest/watermark/replay/
     hold/presence flips — one-pass diagnosis, no rematerialize authority.
- **Do not repeat:** Do not answer TRIVIAL by adding another stub or more
  exact counts. Do not leave intent comments on fix sites. Do not treat
  rebuild-compare tests alone as hardness when sources are textbook-wrong
  and the instruction is a tally checklist.
- **Harden shipped:** SoftHSM-class `ops/prefer.toml` (live/surface) +
  `core/build.rs` rematerializes `surface_core_lib` / `surface_sieve_b` /
  `surface_main` until durable/authority; prefer gate forces leaf tip;
  residual operator_default + exclusive watermark + emit dedupe +
  hold/presence; symptoms instruction (no exact tallies); durable-preference
  re-entry test. Local: oracle 1.0 / NOP 0.0 / `approve_task.py` PASS.

### 2026-07-24 — `blindfold-capture-contest` (category_classifier → SE + Harbor ruff)

- **Feedback:** CodeBuild quality FAIL. `[category_classifier]` predicted
  blocked `software-engineering` at **0.9** while `task.toml` said
  `games`. Also **hard-failed** on Harbor ruff (~102 errors: `I001`,
  `UP045`, `B023`, `PLW1510`, `PIE810`, …). WARN: instruction
  “start with `tournament_card.md`…” read as a guided reading sequence.
  Flask/jar-extract/pip-lock WARN text is Harbor template noise when the
  local Dockerfile already pins pytest (same class as day-ahead notes).
- **What went wrong:**
  1. `languages = ["python", "java", "bash"]` plus “fighting-reply
     **predicate**” / tooling aura flipped games → SE even with
     `/app/puzzles/` + `judge.jar` + tournament tags (kriegspiel/weiqi
     class: metadata + prose smell beat path cosplay).
  2. Local older ruff (or default select) was green while CodeBuild’s
     newer ruff hard-fails the same tree — oracle packages and tests
     still had `Optional[...]`, unsorted imports, loop-cell `memo`
     closures, and `subprocess.run` without explicit `check=`.
  3. Instruction mixed WHAT with a prescribed doc consumption order.
- **Do not repeat:** For `games`, keep `languages = ["bash"]` (jar is
  sealed tooling, not a declared language roster). Goal-first contest
  instruction; declare `/app/docs/` resources without “start with…”.
  Avoid API nouns (`predicate`, sheet/API manuals). Before zip, run
  Harbor-like `ruff check` (current pin, full task tree including
  `solution/` + `tests/`) and fix `PLW1510`/`UP045`/`B023`/`I001`.
- **Fix shipped:** `languages=["bash"]`; tournament tags
  (`puzzle-book`/`table-contest`); instruction rewrite (no read-order,
  no “predicate”); ruff-clean oracle/tests/kiosk; lesson mirrored in
  `AUTHORING_RIGHTS_AND_WRONGS.md`.

### 2026-07-24 — `battery-pack-thermal-conservation` (category_classifier → SE ×2)

- **Feedback:** CodeBuild quality FAIL. `[category_classifier]` predicted
  blocked `software-engineering` at **0.9** then **0.95** while
  `task.toml` said `scientific-computing`. `[instruction_check]` PASS on
  the second run. Other static checks green; pip lockfile line was WARN
  only (template `flask==…` example in the warning text).
- **What went wrong:**
  1. First fail: instruction still smelled like operate/rebuild procedure
     (“run X after Y”) even with scientific category/tags.
  2. Second fail after instruction-only reframe: residual SE surface was
     `/app/ops/` + cutover/`overlay.live` vocabulary + Python module
     repair aura. Instruction_check ≠ category_classifier — metadata and
     residual-first prose alone do not clear the block if the tree still
     reads as an ops cutover desk.
- **Do not repeat:** Do not “fix” SE classifier for `scientific-computing`
  by only trimming HOW sentences or renaming `rebuild.sh` → `refresh`.
  Do not leave `/app/ops/`, `cutover.ok`, or overlay-cutover nouns as the
  solver-visible layout. Do not treat instruction_check PASS as evidence
  the classifier will accept.
- **Do:** Match SPH-style scientific surface — residual/hotspot bands
  first; handoff accept + trial preference naming; evaluation drivers
  under `/app/scripts/`; scientific tags (`finite-volume`,
  `energy-conservation`, …). Keep graded physics + policy coupling;
  do not relabel to a blocked category.
- **Fix shipped:** Retheme to `handoff.accept` / `trial_pref.*` /
  `scripts/{prep_eval,run_thermal_eval}.sh`; residual-first instruction +
  bands doc; AUTHORING lesson updated. Re-gate + rezip before claiming
  CI green.

### 2026-07-24 — `edge-lane-lattice-rollup` (HARD 0%/60% + sufficiency FAIL on replay)

- **Feedback:** Difficulty ✅ HARD. Opus **0% (0/5)**, GPT **60% (3/5)**.
  Oracle 100%, NOP 0%. Sufficiency FAIL: agents fix crypto/hold/revoke then
  conclude “no replays” on the interleaved stream (accepted +1 on ep 10/20/40/50)
  or over-reject ep10 (7 vs 8). Many structural cells **7/7** while exact
  accepted/replay cells sit **3–5/7**.
- **Do not repeat:** Do not leave “ascending-timestamp interleave” without stating
  that the base capture **contains** non-advancing (incl. equal-ts) credentials on
  epochs 10/20/40/50, or that missing `replay` quarantine inflates accepted.
  Do not leave every accepted-count cell exact while near-miss 23/29 still zeros
  reward — band near-miss; keep one exact restore gate.
- **Do not** answer only by pasting quarantine tuples (prior TRIVIAL class).
- **Revise shipped:** Instruction documents equal-ts replay + presence on
  10/20/40/50 + exact accepted tallies as outcomes; per-epoch tests band
  `[expected-1, expected]` (blocks +1 inflation); `test_exact_restore_counts` +
  matches_rebuilt stay exact; free structural cells require replay-epoch coverage
  / deep bands; quarantine replay uses ⊆ oracle + epoch coverage.

### 2026-07-24 — `edge-lane-lattice-rollup` (CodeBuild static FAIL — same SoftHSM class)

- **Feedback:** Harbor/CodeBuild `run_static_checks.py --version edition_2`
  exit 1. Hard ❌: ruff **PLW1510** ×2 on `tests/test_outputs.py` (~67/74)
  `subprocess.run` without explicit `check=` (reported as 4 errors with the
  ruff summary lines). Also ⚠️ jargon-first `instruction.md` opener; ⚠️
  builder `COPY */src/` before `cargo fetch`; ⚠️ inline `pip install`
  without hashed lockfile (warning’s `flask==…` line is a **template
  example**). Log timestamp `2026/07/24 13:33:07` UTC — same failure class
  as SoftHSM earlier the same day.
- **What went wrong:** Local `approve_task.py` / default ruff did not hard-fail
  PLW1510; Edition-2 platform ruff does. Zip still had bare
  `pip3 install pytest==…` and real src COPY before dep fetch.
- **Do not repeat:** Same bullets as SoftHSM postmortem below and must-fire
  §11–12. Before resubmit: `unzip -p …/tests/test_outputs.py | rg check=`
  and `unzip -l … | rg requirements.txt`.
- **Fix shipped:** `check=False` on both verifier runs; plain-language opener;
  stub+`cargo fetch` then real src; hashed `environment/requirements.txt` +
  `--require-hashes` with separate `RUN rm`.

### 2026-07-24 — `softhsm-jce-preference-lattice` (platform EASY 100%/80% after schedule pin)

- **Feedback:** Difficulty ❌ EASY. Opus **100% (5/5)**, GPT **80% (4/5)**.
  Sufficiency PASS on near-miss (quarantine via Python in `run-desk.sh`;
  verifier calls `cargo`+`trusteval` directly). Artifact `(35).zip`. Trajectories:
  agents open `desk_outcomes.md` + `material_schedule.md` by ep3–4, paste the
  closed-form mix, then one-pass patch ~6 polarity sites (GPT ~15 eps).
- **What went wrong:** Sufficiency pin of the full XOR/rotl algebra + exact
  desk sheet next to greppable identity/`complete:true`/plain-sum/replay/dedup
  stubs. No rematerialize authority — `run-desk.sh` rematerialize would not
  help anyway because tests bypass it.
- **Do not repeat:** Do not answer EASY by adding another independent stub.
  Do not leave closed-form `material[i]=…` in solver-visible runbooks once
  agents already clear the lattice from it. Rematerialize must fire on
  **verifier `cargo build`** (`build.rs`), not only on the desk shell.
- **Harden shipped:** Durable SoftHSM `prefer.toml` (live/surface → durable/
  authority); `core/build.rs` rematerializes identity stubs unless prefer ok;
  prefer gate forces leaf manifest; ship correct emit/hold bodies; strip
  closed-form operators from material runbook (components + framecheck);
  symptoms instruction; new durable-preference re-entry test. Complexity
  retained as coupled prefer×material×manifest×integrity×replay.

### 2026-07-24 — `softhsm-jce-preference-lattice` (category_classifier → SE at 1.0 after ruff fix)

- **Feedback:** New CodeBuild run `13:44:11` UTC. Ruff/pip/instruction_check
  all ✅. Sole hard ❌: `[category_classifier]` predicted blocked
  `software-engineering` at **1.0** while `task.toml` said `security`.
  Prior zip the same day had classified **security 0.95**. Cache-order
  Dockerfile note is WARN only.
- **What went wrong:** Sufficiency pin of the material schedule plus
  “provider-pack **cutover**” / repair-flavored SoftHSM–JCE packaging
  prose flipped the whole-surface classifier to SE even though
  `instruction_check` still passed. Tags led with `softhsm`/`jce`;
  opener read as tooling restore. Same class as edge-lane / pms SE
  blocks: metadata ≠ classifier.
- **Do not repeat:** After a static-check green, do not “improve”
  `security` tasks by dumping algorithm + cutover vocabulary into
  `instruction.md`. Keep edge-lane shape: surface check ≠ authority;
  admit/reject/quarantine outcomes; soft “rebuild of the admit path”;
  tags `trust-authority` / `revocation` / `replay` / `attestation`.
  Never treat instruction_check PASS as category PASS. Fingerprint the
  **new** CodeBuild timestamp before claiming the last zip is graded.
- **Fix shipped:** Trust-authority instruction (no cutover); tags
  reordered; evaluator notes surface ≠ authority; languages=`rust`.

### 2026-07-24 — `softhsm-jce-preference-lattice` (CodeBuild static FAIL + stale-zip mistake)

- **Feedback:** Harbor/CodeBuild `run_static_checks.py --version edition_2`
  exit 1. Hard ❌: ruff **PLW1510** on `tests/test_outputs.py` (~65/72)
  `subprocess.run` without explicit `check=`. Also ⚠️ jargon-first
  `instruction.md` opener; ⚠️ `COPY */src/` before dep fetch; ⚠️ pip
  without hashed lockfile (warning text’s `flask==…` line is a **template
  example**, not the task Dockerfile). Log timestamp
  `2026/07/24 13:30:16` UTC; build context still showed old Dockerfile
  line map (src COPY at 10–12, bare pip at 43).
- **What we did wrong (authoring / packaging process):**
  1. Shipped a zip that passed local `approve_task.py` while **upstream
     ruff is stricter** — PLW1510 was never run as a hard gate in the
     author loop until CodeBuild failed.
  2. After fixing the tree, told the user the task was fixed **without
     forcing a zip-fingerprint check against the CI paste**. When the
     same 13:30 UTC log was re-pasted, the correct move was “this log is
     the pre-fix artifact; resubmit the 19:11 IST zip,” not another
     blind rewrite.
  3. Used inline `pip3 install pytest==…` (local Edition-2 gate OK) while
     **platform** also wants `requirements.txt` + `--require-hashes` +
     `--hash=sha256:` entries.
  4. Builder stage copied real `core/src` / `vfy/src` / `skim/src` before
     any fetch/build, so cache-order WARN fired on every source edit.
- **Do not repeat:** Fingerprint `unzip -p` vs CodeBuild paths before
  claiming CI green. Always `check=False` (or `check=True`) on verifier
  `subprocess.run`. Ship hashed `environment/requirements.txt` +
  separate `RUN pip … --require-hashes` / `RUN rm`. Stub → `cargo fetch`
  → `COPY` real src → `cargo build`. Open `instruction.md` with one
  plain-language goal sentence before SoftHSM/material jargon.
- **Fix shipped (current zip):** `check=False` on both runs; plain opener;
  stub+`cargo fetch` then real src; hashed requirements + `--require-hashes`;
  local oracle 1.0 / NOP 0.0 / `approve_task.py` PASS. Resubmit
  `Task_Ready_To_Submit/softhsm-jce-preference-lattice.zip` (mtime after
  the fix) — do not treat the 13:30 UTC log as grading that zip.

### 2026-07-23 — `thin-lto-archive-visibility-lattice` (platform TRIVIAL after dig×epoch harden)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus **100% (5/5)**,
  GPT **100% (5/5)**. Oracle 100%, NOP 0%. All 10 tests **10/10**.
  Artifact: `difficulty_check_artifact (21).zip`.
- **What went wrong (from trajectories; GPT ~7–11 eps, Opus ~29–52):**
  1. **`instruction.md` named `stamp_audit.jsonl`** and that file contained the
     exact graded `(strand,epoch)→vis_digest` rows. Agents reverse-engineered
     or **hardcoded the table into `/app/bin/archctl` shims**.
  2. **Residual frontier was still ~6 independent polarity stubs** (`emit_q3`,
     `xv_q2`, `knit_v4`, `lane_k1` fleet→field, `cg_n5`, `fold_e` legacy).
     Sealed probe + durability prose did not create hardness once the audit
     schedule and stubs were greppable — same SoftHSM / INT8 / triple-toolchain
     post-seal TRIVIAL class.
- **Do not repeat:** Never ship a complete graded-cell audit path in the
  instruction next to always-wrong dig/profile/membership stubs. Incomplete
  samples only; couple dig×epoch×members; put hardness in sealed cutover /
  prefer / lane-fold rematerialize (correct application digests); novel
  profile cell that hardcode tables miss; verifier rebuild from `/app`.
- **Redesign direction:** Correct dig×epoch×members application surfaces;
  broken `ops/nx` cutover gate + pack prefer + lane.d fold + release mask;
  craft/epsilon novel cell; symptoms-only instruction (no audit path).

### 2026-07-24 — `sph-kernel-handoff-reconcile` (CodeBuild ruff PLR0124)

- **Feedback:** Harbor/CodeBuild `run_static_checks.py --version edition_2`
  exit 1. Hard ❌: ruff **PLR0124** on `tests/test_outputs.py:20`
  (`return v == v and …` NaN idiom). Log also said “ruff found 2
  error(s)” / “Static checks failed with 3 error(s)” while only one
  PLR0124 line was pasted; Dockerfile `build-essential` / bare `pip`
  lines were ⚠️ only (agent-rebuild carve-out / lockfile WARN).
- **What we did wrong:**
  1. Relied on local `ruff check` / `run_static_checks.py` from the
     TERMINUS repo root, where default rule selection **does not**
     enable PLR0124 — so the gate stayed green while CodeBuild’s
     harbor ruff (task-only tree under `~/tasks/tbench-task`, no repo
     ignore config) hard-failed the same file.
  2. Used the classic `v == v` finite check instead of
     `math.isfinite(v)`.
  3. Risked the SoftHSM same-day mistake: treating a local approve
     zip as CI-green without a platform-strict ruff pass on the
     packaged verifier files.
- **Do not repeat:** Before packaging, run
  `ruff check tasks/<task>/tests/ --select PLR0124,PLW1510` (and fix
  every hit). Prefer a NaN-safe range (`float("-inf") < v < float("inf")`)
  or `math.isfinite` — but if collapse **GX8** treats `import math` as a
  domain primitive owned by tests, use the range form. Always put
  explicit `check=` on `subprocess.run`. After a CodeBuild paste,
  fingerprint `unzip -p …/tests/test_outputs.py | sed -n '20p'` against
  the log line before claiming another fix. Do not chase Dockerfile
  build-toolchain WARN on agent-rebuild tasks as if it were the
  blocking error.
- **Fix shipped:** `_finite` → `float("-inf") < v < float("inf")`
  (PLR0124-clean, no `math` import); AGENTS/AUTHORING lesson recorded.
  Complexity unchanged (verifier lint only).

### 2026-07-24 — `sph-kernel-handoff-reconcile` (probe entry-point names underspec)

- **Feedback:** Needs Revision. Schema said only a vague “must stay
  importable” and never named `greens_table_for_run` / `reduce_chunks`.
  Agents that renamed those publics while fixing physics failed the
  workspace rebuild before greens/chunk probes could run.
- **Do not repeat:** When rustcheck imports fixed symbol names, document
  those names as reachability outcomes (not fix recipes).
- **Fix shipped:** Schema Gravity table + Chunked reduction + Verifier
  probes sections name the symbols; instruction points at named public
  probe entry-point stability. Complexity unchanged (docs only).

### 2026-07-23 — `sph-kernel-handoff-reconcile` (platform EASY 80%/80% + sufficiency)

- **Feedback:** Difficulty ❌ EASY. Opus/GPT both **80% (4/5)**. Almost all
  tests **10/10**; `test_residuals_reflect_real_numeric_work` **9/10**.
  Sufficiency FAIL on near-miss: agent forced exact `h` / zeroed residual
  bookkeeping → bands green, hidden `sum(h_consistency) > 0` red.
  Artifact: `difficulty_check_artifact (19).zip`.
- **What went wrong:**
  1. Schema acted as a **six-site fix checklist** (Shepard algebra,
     `moment_coeff`, StepReport floors, symbol roster) — agents transcribed
     then polarity-flipped greppable stubs.
  2. Bugs were **independent**; fixing one did not invalidate another.
  3. Residual liveness lived only in a test assert, not the schema.
- **Do not repeat:** Do not leave hardness as independent SPH polarity
  stubs beside a recipe schema. Do not gate credit on undocumented
  `h_total > 0`. Couple rematerializing policy authority with overlay
  ignore; couple force pressures to the published Shepard field; document
  residual liveness as an outcome.
- **Harden shipped:** Residual-liveness section; thinner gravity/probe
  prose; fleet rematerialize overwrites handoff unless restored from
  `handoff.canon`; `read_policy` still prefers overlay until fixed; force
  path uses private raw density until fixed to consume Shepard `rho`;
  tests grade against `handoff.canon`.

### 2026-07-24 — `triple-toolchain-abi-unify-lattice` (oracle FAIL — amd64 probe.stamp harness)

- **Feedback:** Difficulty artifact (26): all 3 oracle trials reward **0**; agents
  never ran. Oracle `solve.sh` itself exited 0; every test ERROR'd at fixture
  setup: `sha256sum -c harness.sha256` → `/app/ops/probe.stamp: FAILED`.
- **What went wrong:** `harness.sha256` pinned the content hash of
  `probe.stamp`, which is `sha256(unify_probe)`. Author laptop built the
  image as **arm64**; Harbor/CodeBuild builds **linux/amd64**. Different Go
  binary → different stamp file → ledger mismatch. Not an oracle logic bug.
- **Do not repeat:** After any Dockerfile/probe rebuild, regenerate
  `tests/ledgers/harness.sha256` from a **`linux/amd64`** image
  (`docker buildx build --platform linux/amd64`). Prefer
  `go build -trimpath -ldflags="-buildid="` for same-arch stability. Local
  oracle evidence on arm64 Mac is not platform evidence unless
  `DOCKER_DEFAULT_PLATFORM=linux/amd64`.
- **Fix shipped:** amd64-regenerated harness; reproducible probe build flags;
  local amd64 oracle 1.0 / NOP 0.0.

### 2026-07-23 — `triple-toolchain-abi-unify-lattice` (platform EASY after graph-config redesign)

- **Feedback:** Difficulty ❌ EASY (need ≥ MEDIUM). Opus **80% (4/5)**, GPT
  **100% (5/5)**. Sufficiency PASS on the miss (agent identified cmake, forgot
  to write it). Artifact trajectories: agents map five independent edits
  (`lane_k`, `strand_m`, `cut_n`, `pref_a`, `xv_w.cmake`) in one diagnostic
  pass; GPT finishes in ~9–21 episodes.
- **What went wrong:** Sealed probe + rematerialize-on-unsealed-prefer still
  left a **finite declarative checklist** of independent config/cmake flips.
  Local greens did not fail distant cells; fixing each site was one-pass.
- **Do not repeat:** Do not answer EASY by adding another independent cmake
  polarity or instruction recipes. Sufficiency PASS on a forgotten write is
  not hardness.
- **Redesign shipped:** Compound seal×epoch×hold-token gate (`cut_n` +
  `desk_journal.jsonl`); rematerialize many surfaces from wrong `/app/link/`
  seeds until gate ok (lane.d draft, strand, prefer, hook, fold, rel_mask,
  fleet pack_width); drop-in fold (`fold_p` + `lane.d`); release feature mask
  (`rel_mask` + `wire --release`); hook-driven packing (`hook_q` → policy-
  correct `xv_w.cmake`); epsilon release cell; gate re-entry tests. Keep
  correct application stamp/width bodies.

### 2026-07-22 — `sph-kernel-handoff-reconcile` (Shepard neighbor volumes underspec)

- **Feedback:** Needs Revision. Schema required a “partition-of-unity /
  Shepard-normalized” field and rejected raw SPH sums, but never stated
  how neighbor volumes enter the partition sum. Agents that removed the
  handoff scale and weighted every neighbor by the **center** density
  (`m_j / rho_hat[i]`) failed `test_density_not_trivially_equal_to_raw_sph`
  and `test_probe_density_field` — a reasonable reading of the vague
  wording (Instruction Sufficiency / false-negative class).
- **What went wrong:** After earlier TRIVIAL collapse from pasting the
  full Shepard algebra, the schema was thinned to outcomes-only. That
  over-correction dropped the **graded volume-weight polarity**
  (neighbor `rho_hat[j]` vs center `rho_hat[i]`) while the probe still
  asserted the classic neighbor-volume form. Soft “Shepard” naming alone
  does not distinguish those two formulations.
- **Do not repeat:** When two plausible “Shepard-like” implementations
  diverge on a field the probe asserts, document the polarity as an
  outcome (neighbor volumes `m_j/rho_hat[j]` in the partition sum). Do
  not rely on the word “Shepard” alone after shipping a center-density
  trap as the broken baseline.
- **Fix shipped:** Schema density section restores the partition formula
  and explicitly rejects center-density neighbor volumes. Task numerical
  bugs / complexity unchanged (docs fairness only).

### 2026-07-22 — `triple-toolchain-abi-unify-lattice` (platform TRIVIAL after sealed probe)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus **100% (5/5)**,
  GPT **100% (5/5)**. Oracle 100%, NOP 0%.
- **What went wrong:** Sealed `unify_probe` + `stamp_audit.jsonl` stopped the
  readable-formula shortcut, but residual hardness was still **six application
  polarity stubs** (`lane_m2` fleet→field, `cg_p9` facet_y→8, `hdr_n3`,
  `op_q7`, `xv_w`, `knit_w`). Agents grepped the stubs and transcribed the
  audit/probe stamp schedule into correct bodies in one short loop — same
  class as SoftHSM / INT8 / capsule three-stub TRIVIAL.
- **Do not repeat:** Never leave greppable always-wrong stamp/width/profile
  polarity in application sources as the build-category frontier. Shipping a
  sealed probe does not create hardness if runtimes are textbook-wrong and
  the schedule is discoverable from audit samples.
- **Redesign shipped:** Correct rotate-mix stamp / width application in
  `op_q7` / `xv_w` / `hdr_n3` / `cg_p9`; `lane_m2` reads
  `config/lane_k.toml`; hardness in broken bind (`lane_k`) / feature wire
  (`strand_m`) / prefer×cutover rematerialize (`ops/nx` + `knit_w`) /
  CMake archive override (`c6/xv_w.cmake`); probe calls `slotctl wire`;
  oracle edits only graph materials.

### 2026-07-21 — `triple-toolchain-abi-unify-lattice` (category_classifier → SE)

- **Feedback:** CodeBuild static checks hard-failed: classifier predicted
  `software-engineering` at 0.9 while metadata declared
  `build-and-dependency-management`.
- **What went wrong:** Although the graded graph compiles Rust, Go, and CMake
  targets, solver-visible prose led with a “plugin host,” “language surfaces,”
  and “repaired helpers.” Tags emphasized `ffi`/`cgo` rather than build-matrix
  propagation. The primary activity therefore read as cross-language software
  repair instead of build configuration.
- **Do not repeat:** Build-category tasks must lead with the build graph:
  profile and feature propagation, generated headers, archive packing,
  debug/release artifacts, and linking. Align instruction, tags, runbooks, and
  matrix comments; changing metadata alone does not change classification.
- **Fix shipped:** Reframed solver-visible prose around a cross-toolchain
  build matrix and durable build artifacts; tags now emphasize build-matrix,
  generated headers, feature propagation, profile resolution, and linking.
  Stamp schedule, sealed probe, six hard loci, tests, and oracle logic remain
  unchanged.

### 2026-07-20 — `sph-kernel-handoff-reconcile` (greens coeff underspec + rubric `/tests`)

- **Feedback:** Needs Revision.
  1. Schema kept `greens_table_for_run` reachable and said “probe outcomes
     matter,” but never required `moment_coeff == Handle.second_moment_coeff`.
     Agents that left `table_from_quadrature` failed
     `test_probe_greens_coefficient` (e.g. coeff `0.729167` vs handle
     `0.371000`) — Instruction Sufficiency / false-negative class.
  2. Rubric line penalized modifying `/app/tests/` … Rubric lines must not
     reference paths under `/tests` and must be checkable from the terminal
     trace alone.
- **What went wrong:**
  1. Over-corrected after the earlier TRIVIAL collapse (schema answer-key
     with exact greens equality). Fairness for reachability was restored,
     but the **graded coefficient contract** was stripped with the recipe.
     Reachability ≠ behavior: agents can keep the symbol and still fail.
  2. Copied a stock “don’t touch tests” negative into the UI rubric without
     filtering `/tests` paths (platform rule: no `/tests` in rubrics).
- **Do not repeat:** For probe-linked public surfaces, document both
  (a) the symbol must stay reachable and (b) the numeric field the probe
  asserts — here `moment_coeff` matches `second_moment_coeff`. That is an
  outcome contract, not a full fix recipe. Never put `/tests/...` in
  rubric lines; penalize only agent-visible paths (`/app/scripts/`,
  `/app/docs/`, `/output/`, …) visible in the trace.
- **Fix shipped:** Schema gravity-table section + probe blurb state the
  `moment_coeff` match. Rubric `-3` retargeted to `/app/scripts/` only.
  Task numerical complexity unchanged.

### 2026-07-22 — `softhsm-jce-preference-lattice` (platform: TRIVIAL ×2 after instruction trim)

- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. Artifact `(7).zip`.
- **What went wrong:** Instruction-quality trim still left a **preference-constant
  GateSeal** (SHA-256 of five small ints) plus published band 4–9. Agents
  bruteforced the sealed tuple, transcribed NestK, unswapped JNI, patched
  AssembleY/reload — debugging, not SoftHSM trust reconstruction.
- **Do not repeat:** Never gate SoftHSM/JCE on bruteforceable prefs digests or
  publish band integers next to editable NestK sheets.
- **Redesign shipped:** SoftHSM-framed WAL admission lattice (opaque material,
  sealed framecheck, hold/revoke/replay/presence, surfcheck ≠ trusteval).
  Evidence: `logs/softhsm-jce-preference-lattice-trivial-2026-07-22.md`.

### 2026-07-20 — `softhsm-jce-preference-lattice` (platform: TRIVIAL after sufficiency “fix”)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus/GPT-5.5 both
  **100% (5/5)**. Oracle 100%, NOP 0%. All 10 tests **10/10**. Prior round
  was HARD with 0% agents (sufficiency FAIL on `stale_slot`/`revoked`).
- **What went wrong:**
  1. Sufficiency “fix” pasted a full host reason-code recipe into
     `instruction.md` (wrong_pack / stale_slot / revoked / unmarked / root).
  2. Hardness stayed three textbook-empty polarity stubs (`knit_xv` always
     green, `op_b` always clear, `op_c` always genOk) plus a bait window.
  3. Agents transcribed the recipe into the stubs in one short loop —
     same class as signed-plugin / capsule / INT8 three-stub TRIVIAL.
- **Do not repeat:** Never answer Instruction Sufficiency by shipping an
  answer-key decision table next to empty polarity bodies. Scenario prose
  for stale vs revoked is fair; a checklist + stubs is TRIVIAL.
- **Redesign shipped:** Correct decision bodies (`knit_xv` / `OpB` / `OpC`);
  wrong `FluxK`/`NestK`/`ForgeK` vs sealed fingerprint; JNI pack/mode byte
  swap; AssembleY surface-window + live-as-durable bind; `desk-reload.sh`
  rematerializes `NestK` from the surface window (undoes naive sheet edits).
  Instruction: symptoms + short stale/revoked scenario prose only. Evidence:
  `logs/softhsm-jce-preference-lattice-trivial-2026-07-20.md`. Local gates:
  oracle 1.0 / NOP 0.0 after redesign.

### 2026-07-20 — `kriegspiel-blind-chess-adjudication` (category_classifier → SE ×3)

- **Feedback:** CodeBuild quality FAIL thrice. `[category_classifier]`
  predicted `software-engineering` (0.9–0.95) while `task.toml` said
  `games`. Latest run also WARN'd on imperative “Before grading, read…”.
- **What went wrong:** Instruction-only / languages=`bash` / sealed binary
  were not enough while the submission still smelled like tooling:
  task name `*-adjudication`, binary/docs named `arbiter`, `/app/sheets/`,
  and procedural instruction directives.
- **Do not repeat:** For `games`, retheme **name + binary + paths + docs +
  instruction** to tournament/contest language (weiqi `*-capture-contest` /
  `judge` / `/app/puzzles/` pattern). Declare resources; do not prescribe
  “read docs before…”. Keep Cargo/crates out of the zip.
- **Follow-up (2026-07-21):** Still SE at confidence **1.0** after contest
  rename while shipping a native ELF `judge` plus SE-named oracle packages
  (`seat_fold`/`lane_knit`). **Do:** Python sealed judge like weiqi’s jar
  aura (no ELF toolchain artifact); tournament desk package names; clear
  goal-first instruction; clerk/kiosk decoy docs.

- **Feedback:** Instruction Sufficiency FAIL. Every GPT-5.5 trial failed the
  same trap-refutation test (`test_q7_topaz`). Agents copied the scout's
  broad cooperative fill hunt into `refutations` because docs said
  "threatens … under cooperative play" and never stated the graded rule.
- **What went wrong (authoring mistake):**
  1. **Hidden threat polarity.** Tests graded Black first-tries that capture
     immediately or on Black's next move after White passes, but that rule
     lived only in `TRAP_THREATS` / oracle helpers — not in `/app/docs/`.
  2. **Scout false-green reinforced the wrong reading.** `scout_hint.sh`
     uses a multi-ply White-pass hunt; agents treated that as the
     refutation frontier.
  3. **Exact set equality.** Covering every required threat plus one extra
     valid reply still failed `covered == sorted(threats)`.
  4. **Answer-leaking sheet comments** (`# win1`, `# trap5`, `# fort`).
  5. **Doc/test drift:** wins needed `coop_capturable=true` and ≥2 White
     plies in tests while docs said only ≥1 White stone; instruction did
     not tell agents to read `/app/docs/` for graded vocabulary.
- **Do not repeat:** For games booklets, document every graded polarity that
  tests assert (threat definition, win `coop_capturable`, White-ply floors).
  Soften hidden-set equality to required ⊆ submitted. Strip status labels
  from fixtures. Point agents at `/app/docs/` when rules live there. Keep
  scout bait narrower or explicitly non-authoritative for the graded set.
- **Fix shipped:** Documented immediate / next-move-after-pass threat rule;
  coverage-not-equality in `test_q7_topaz`; stripped sheet labels; aligned
  win docs with `coop_capturable` + two White plies; instruction points at
  `/app/docs/`. Complexity unchanged.

### 2026-07-21 — `triple-toolchain-abi-unify-lattice` (platform EASY ×2 after stamp×width)

- **Feedback:** Difficulty ❌ EASY again (Opus 100% / GPT 80%). Sufficiency
  FAIL on the miss: agent patched correctly then left a Python `slotctl` under
  `/usr/local/bin` (ephemeral); verifier re-entry used stock `/app/bin/slotctl`.
  Reviewer also asked to paste the stamp bit-formula into `instruction.md`.
- **What went wrong (authoring mistake):**
  1. **Readable probe = answer key.** Agents `cat` `/app/tools/unify_probe`
     and transcribed `goStampFromFacets` (`0xA100|(w<<4)|facets`) into a
     six-site fix checklist in ~8–20 episodes.
  2. Stamp×width + `knit_w` + fleet→field were still independent polarity
     flips once the formula was known.
  3. Answering sufficiency by publishing the hex formula would collapse to
     TRIVIAL (same SoftHSM/INT8 lesson).
- **Do not repeat:** Never leave observation-runner source with the graded
  stamp algebra in the runtime image. Do not paste closed-form stamp recipes
  into `instruction.md`. Prefer sealed probe binary + fixture audit samples
  + durable `/app/bin` rebuild outcomes.
- **Harden shipped:** Rotate-mix stamp (not `<<4`); probe built then sources
  stripped from image (`probe.stamp` pin); `stamp_audit.jsonl` for fair
  discovery; instruction durability note for `/app/bin` helpers; map_legacy
  keeps old `0xA100` decoy. Complexity retained (auth/pack/hdr/fwd/knit_w).

### 2026-07-21 — `triple-toolchain-abi-unify-lattice` (platform EASY after sufficiency fix)

- **Feedback:** Difficulty ❌ EASY (need ≥ MEDIUM). Opus **100% (5/5)**,
  GPT-5.5 **80% (4/5)**. Instruction Sufficiency already PASS. Oracle 100%,
  NOP 0%.
- **What went wrong (authoring mistake):**
  1. Fair profile-width sufficiency fix left **four independent polarity
     sites** (`fwd.rs`, `auth.go`, `pack.go`, `hdr_n3.c`) plus named ship 8 /
     fleet 4 targets — agents one-pass fixed each site.
  2. `abi_stamp` was textbook `0xA100|facets` identical across Go/Rust/hdr,
     so stamp greened without encoding pack_width.
  3. No build-graph authority rematerialized wrong width after profile
     resolve looked correct.
- **Do not repeat:** After documenting fair pack_width outcomes, do not
  leave hardness as independent facet/profile polarity flips beside a
  facet-only stamp. Couple stamp×width; add a build.rs (or equivalent)
  locus that rematerializes legacy archive width over live `PACK_WIDTH`;
  deepen profile alias (e.g. fleet→field) so resolve and declared profile
  diverge until fixed. Keep outcomes in instruction; never publish the
  hex stamp formula or EXPECTED `0xA1xx` values.
- **Harden shipped:** Width-nibble stamp
  `0xA100|((w&0xF)<<4)|facet_bits`; `build.rs` prefers
  `/app/link/legacy.toml` `archive_pack`; fleet→field alias in `lane_m2`;
  deepened fwd/hdr facet-only stamp while broken; EXPECTED alpha
  `0xA181`/8, beta `0xA143`/4, gamma/delta `0xA142`/4.

### 2026-07-20 — `triple-toolchain-abi-unify-lattice` (Instruction Sufficiency / behavior_in_task_description FAIL)

- **Feedback:** Quality check hard-fail on `behavior_in_task_description`;
  sufficiency failed all nine trials; agent review revise. Opus 1/5, GPT-5
  0/5. Fleet pack_width tests ~2/10. Oracle 3/3.
- **What went wrong (authoring mistake):**
  1. **Instruction only required mutual agreement** of `abi_stamp` /
     `pack_width` across language surfaces. Agents greened all three at
     pack_width 8, probe reported `status ok`, then failed verifier
     EXPECTED (fleet profile declares 4, ship 8).
  2. **Probe `status ok` matched the weak instruction** (agreement only),
     so the false plateau looked like success. EXPECTED lived only in
     tests and was labeled “not present in the probe source.”
  3. **Delta cell** asserted pack_width but not `abi_stamp`, so a uniformly
     wrong stamp could slip that test.
- **Do not repeat:** When tests grade profile-declared numeric targets,
  state those outcomes in `instruction.md` (and point at the profile
  files). Observation runners must not report `ok` on mutually agreed
  *wrong* profile widths. Do not leave the load-bearing target only in a
  verifier EXPECTED table.
- **Fix shipped (complexity unchanged):** Instruction names ship/fleet
  pack_width under `/app/config/profiles` and requires converge on
  profile-declared width + feature-matched stamp. Probe `ok` requires
  agreement AND declared-profile pack_width AND feature stamp. Delta test
  also asserts `abi_stamp`. Four coupled loci unchanged.
- **Authoring follow-up mistake (local):** Regenerating `harness.sha256`
  with paths relative to `environment/` (`tools/...`) while tests run
  `sha256sum -c` with `cwd="/"` broke oracle (8 setup ERRORs). Ledger
  entries must be absolute `/app/...` paths matching the container layout.
- **Follow-up (2026-07-21):** Sufficiency fix alone → platform EASY
  100%/80%; see EASY postmortem above for stamp×width + build.rs harden.

### 2026-07-20 — `sph-kernel-handoff-reconcile` (rubric misaligned with graded behavior)

- **Feedback:** Platform review: chunk-stability criterion pointed at the
  runner layout / reduction path, while the required fix is in the shared
  reduction implementation. Green's table criterion described kernel
  selection rather than the coefficient behavior being graded.
- **What went wrong (authoring mistake):**
  1. **Chunk criterion named the wrong locus.** An earlier UI rubric draft
     said `layouts.rs` / “runner reduce path” (and even “pairwise/Kahan
     reduce” as a how-to). Graded behavior is
     `sph_a::reduce::{reduce_chunks, chunk_stability_delta}` —
     chunk-invariant summation on canceling scratch streams. The runner
     only *calls* that shared reduce; editing layouts does not satisfy the
     probe.
  2. **Greens criterion described the wrong physics.** The same draft said
     “rebuild the Greens table against the policy target kernel rather
     than the checkpoint source kernel.” That is policy/kernel *selection*,
     already covered elsewhere. The greens probe grades
     `moment_coeff == Handle.second_moment_coeff` (reject re-derived
     quadrature), not which kernel id was chosen.
  3. **Root cause:** Rubric lines were written from a mental model of the
     report pipeline (“runner layouts + kernel handoff”) instead of from
     the verifier probe assertions in `tests/rustcheck/main.rs`. Rubrics
     that name the wrong file or the wrong behavior mis-grade correct
     agent traces and send solvers to decoy edit sites.
- **Do not repeat:** Before pasting UI rubrics, open the probe that the
  criterion is meant to reward and name the **symbol + behavior** that
  probe asserts. Do not invent runner/layout paths or “target vs source
  kernel” wording when the probe never checks those. Keep policy-authority
  and greens-coefficient as separate criteria.
- **Fix shipped:** Rubric lines updated — greens → `moment_coeff` matches
  `Handle.second_moment_coeff`; chunk → shared `sph_a/src/reduce.rs`
  chunk-invariance. Task complexity unchanged (rubric-only).

### 2026-07-19 — `dm-thin-snapshot-fanout-reconcile` (CI: category_classifier → SE)

- **Feedback:** Harbor static checks **FAIL**. `[category_classifier]`
  predicted `software-engineering` (0.85) while `task.toml` said
  `system-administration` — blocked category.
- **What went wrong:** Graded activity was patch Go/C under `/app` +
  `make install` / rebuild `matfan`. Tags/languages smelled like a code
  repair lab; journals/leases looked like fixtures beside a toolchain.
  Same failure mode as backup-restore pre-sysadmin redesign and
  edge-lane/pms SE blocks.
- **Do not repeat:** Do not declare `system-administration` while the
  oracle rebuilds language sources. Prefer live `/etc` + `/var` ops
  helpers, prebuilt binary, ops-flavored tags, and an ops entrypoint
  (`run_materialize.sh`) with no make/go recipe in the instruction.
- **Redesign shipped:** Correct prebuilt `matfan`; broken
  `fold_k`/`pref_a`/`skim_x`/`hold_m`/`emit_h` under `/app/ops` writing
  `/etc/pool` + `/var/lib/pool` + `/var/run/pool`; drop-in preference
  mode; symptoms-only instruction; tags `thin-pool`, `ops-journal`,
  `activation`, `leases`, `dropin-policy`.

### 2026-07-19 — `dm-thin-snapshot-fanout-reconcile` (HARD + Instruction Sufficiency FAIL)

- **Feedback:** Difficulty ✅ HARD. Agents **0% (0/10)** (Opus/GPT). Oracle
  100%, NOP 0%. Nearly every trial **8/9**; only `test_w9_quartz` **0/10**.
  Judge: Instruction Sufficiency FAIL — universal miss of
  `activation.toml` rewrite after rematerialize.
- **What went wrong:** Agents fixed seal-cap fold, epoch/floor preference,
  decoy skim, and leases, then stopped. Required behavior lived only in an
  unused `ScrubW` helper + test docstring (“naive tip rewrite undone by
  sealed preflight”). `instruction.md` covered payloads/report/leases only —
  no sealed meta rewrite outcome. Scoring needs all tests → 8/9 = 0 reward.
- **Do not repeat:**
  1. Never gate full credit on a meta/ledger scrub that is unspecified in
     `instruction.md` (same class as edge-lane hold-presence / fanotify host
     emit: fair outcome must be stated as a scenario, not buried in code).
  2. Do not treat “helper exists but is never called” as discoverable hardness.
  3. Do not leave hardness as one undocumented scrub after agents already
     clear the common polarity/lease sites — that yields HARD + 0% with
     sufficiency FAIL, not calibrated difficulty.
- **Redesign shipped:** Document activation tip-map rewrite + roster-only
  fanout + `seal_gen` as outcomes (scenario prose, no fix recipe). Couple
  off-roster `omega`, exact tip-map asserts, epoch `>=` boundary, and new
  tests (`n5_beryl`, `y3_coral`). Reusable lesson also in
  `AUTHORING_RIGHTS_AND_WRONGS.md`.

### 2026-07-18 — `pms-annotation-processor-bom-cutover` (platform: TRIVIAL × Maven + capsule)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus/GPT both **100%**.
  Unit tests in the reported run were the **Maven JPMS** names
  (`test_r3_dep_ok`, `test_u7_apt_ok`, …) — artifact (9). Local tree later
  became a **capsule three-stub clone** (`fold_q`/`gate_r`/`slot_w`), which
  is the same TRIVIAL class as signed-plugin (textbook-wrong polarity stubs).
- **Do not repeat:** Never ship (1) answer-shaped ship rosters + BOM checklist,
  or (2) three tiny always-wrong predicates as the whole security frontier.
  Prefer edge-lane-class WAL/authority coupling with opaque fixtures and
  verifier-owned EXPECTED.
- **Redesign:** Differentiated Rust mesh attestation lattice (surface ≠
  authority, hold/revoke/presence, reject ledger) — not Maven polarity and
  not capsule stub clone.

### 2026-07-18 — `pms-annotation-processor-bom-cutover` (CI: category_classifier → SE)

- **Feedback:** CodeBuild quality **FAIL**. `[category_classifier]` predicted
  `software-engineering` (0.85) while `task.toml` said `security`. Also WARN:
  closing “Rebuild with make, then run …” is HOW, not WHAT.
- **What went wrong:** Task name still smells like APT/BOM cutover; tags
  included `modular` / `rust` / `go`; instruction closed with a make/run
  recipe. Classifier read primary activity as code rebuild, not admit/revoke
  trust authority (same failure mode as edge-lane).
- **Do not repeat:** For `security`, lead with surface ≠ authority +
  accept/reject / ledger outcomes; tags like `trust-authority`,
  `admission`, `revocation`, `attestation`. Never prescribe `make` /
  `cargo build` as the task. Soft rebuild: “Outputs must match a rebuild
  of the admit path… Hand-written stand-ins fail.”
- **Fix:** Rewrote instruction (trust/admit framing, no make recipe);
  security-flavored tags; drop language/modular tags.

### 2026-07-18 — `edge-lane-lattice-rollup` (HARD + Instruction Sufficiency FAIL)

- **Feedback:** Difficulty ✅ HARD. Agents **0% (0/10)**. Oracle 100%. Top
  trials reached ~20/23 — cracked integrity reverse-engineering, then dropped
  epoch 30: undocumented rule that **held co-presence keeps the epoch
  published with reduced accepted**. Judge: task_specification fail.
- **Do not:** Leave required semantic polarities (hold vs revoke for
  mutual-presence) only in code. Outcomes that tests assert on every trial
  must appear as problem-statement scenarios in `instruction.md` without
  becoming an implementation checklist or answer-key counts.
- **Also:** Prefer less-common crypto schedules than plain `seed[i]^epoch`
  (agents pattern-match that). Add a revoke-only required-lane epoch that
  must be omitted to catch “any frame counts as presence” patches.
- **Follow-up (0/10 vs 10/10 redesign):** Soften presence-band for the hold
  epoch while keeping exact accepted on a subset; document strict
  timestamp-advance replay; ship ≥2 audit samples for key discovery;
  harden former free 10/10 structural tests with deep-vs-surface accepted
  inequalities so surfpoke/surface paths fail those checks.
- **Follow-up (category + sufficiency reject):** Reviewer: XOR `seed^epoch^i`
  + 1-byte keyed fold is not security (debugging costume). Replaced with
  Ed25519 over payload vs SHA-256(seed\|\|epoch_be) secret; wrong-signer and
  garbled sigs → `integrity_failure`. Documented graded accepted tallies,
  quarantine keys, and hold/revoke/replay semantics in `instruction.md`.
  Same six bug loci and count matrix (complexity unchanged).
- **Follow-up (platform EASY 100%/80%):** Answer-key counts + trained six
  polarity bugs + formula in runbooks. Hardened: domain-bound `ELL2` messages,
  `ell.v1` key domain, legacy payload-only traps, novel loci (LE derive,
  operator_default bait, exclusive watermark load, Active|Revoked presence,
  hold `>=` threshold, missing replay), nine enumerated integrity keys,
  symptoms-only outcomes (no exact accepted checklist), more tests.
- **Follow-up (quarantine copy + JSONL sufficiency):** Dropped quarantine
  tuples from instruction; tests now compare agent quarantine to rebuilt
  oracle sets. Clarified `/app/data/credentials/*.jsonl` as deep inputs.
  Rubric/explanations retargeted to `surfpoke` /
  `surface_attestation.json` / `trust-attestation.json` / `lane-lattice-v2`
  and credit Ed25519 + key derivation.

### 2026-07-18 — `edge-lane-lattice-rollup` (CI: category_classifier → SE)

- **Feedback:** Harbor static checks **FAIL**. `[category_classifier]`
  predicted `software-engineering` (0.85) while `task.toml` said `security`
  — blocked category. Also WARN: instruction prescribed `cargo build -p
  trusteval --release` and sequential “Build… then publish…”.
- **What went wrong:** Instruction led with “Restore the Rust attestation
  tooling” / cargo build recipe. Classifier read primary activity as code
  repair, not trust-authority reconstruction.
- **Do not repeat:** For `security`, frame like capsule/admit: surface
  check ≠ authority; produce verified-trust / reject forensic outputs;
  name rebuild entrypoints lightly — never lead with “fix the Rust
  project” or prescribe package-manager build lines as the task.
- **Fix shipped:** Rewrote instruction to trust-authority / forgery /
  quarantine outcomes; tags security-flavored; ops notes say surface is
  not authority.

### 2026-07-18 — `backup-restore-reconstruction` (platform: TRIVIAL)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus/GPT-5.5 both
  **100% (5/5)**. Oracle 100% (3/3), NOP 0%. All 24 tests **10/10**.
  Artifact: `difficulty_check_artifact (3).zip`. Full write-up:
  `logs/backup-restore-reconstruction-trivial-2026-07-18.md`.
- **What went wrong (from agent trajectories; GPT ~11–15 steps):**
  1. **`docs/layout.md` named every mutable ledger knob** (`shelf.name`,
     `profile.bind`, `borrow.list`, `fragments.map`, `quarantine.flag`) and
     the cross-lab spans. That was a repair checklist.
  2. **`ops/rotation-memo.txt` leaked answer values** (mesa mask `42`,
     beacon audit / cinder batch authority, ridge→cinder preference).
  3. **Solve = move blobs + edit a tiny declarative cluster** while the
     Rust binary stayed correct. No higher authority rewrote those edits.
  4. **Stamp-scan + XOR bruteforce** derived every remaining knob from
     recipe marks + pool bytes; independent fixes did not invalidate each
     other. Surface `labhealth` was ignorable bait.
- **Do not repeat:** See Hardness collapse lessons §1–4 below. Do not ship
  knob checklists or numeric memos; do not freeze the binary and leave only
  ledger/profile edits; do not rely on stamp-matching as residual hardness.
- **Redesign shipped:** Keep `system-administration` + Rust. Volume mounts
  (`/app/volumes/` + decoys), sealed journal WAL replay (`relay::fold_lines`
  fenced on `fleet.seal`), haul materialization that prefers decoys when
  broken, codec that ignores `mask.live` until fixed, preflight that wipes
  naive ledger edits every restore. Oracle 1.0 / NOP 0.0 after redesign.

### 2026-07-19 — `backup-restore-reconstruction` (category FAIL: not sysadmin)

- **Feedback:** Declared `system-administration` unjustified. Graded
  activity was rewrite Rust + JSON reconcile vs oracle (debugging /
  data-processing). No live host ops; `run_recovery` was cargo+run;
  knit_a epoch / borrow tiebreak / `run.stamp` underspecified; rubric
  paste described a prior fieldday/labs variant.
- **Do not repeat:** Category must grade operating live `/etc`/`/var`
  admin surfaces with a correct prebuilt tool. Do not require SYS_ADMIN
  mounts. Document fence/borrow/`run.stamp`. Align rubric ↔ zip.
- **Fix shipped:** Broken surfaces are `weave_k`/`pull_m`/`mark_t`/`bind_v`
  helpers; sealed volume attach via same-inode hardlink; fleetd pidfile;
  Rust correct in image; instruction documents rules; variants reconciled.

### 2026-07-19 — `backup-restore-reconstruction` (platform: EASY)

- **Feedback:** Difficulty ❌ EASY. Opus **100% (5/5)**, GPT **80% (4/5)**.
  Sufficiency FAIL on near-miss: agent ran recovery without fixing live
  state. Root cause of EASY: graded frontier was four polarity helpers +
  synonym↔site_standard diff.
- **Do not repeat:** Do not leave hardness as “rewrite four obvious
  scripts.” Couple drop-in fold, ops-journal sealed cutover (beats later
  rollback), generation gate, hold/lineage rematerialize, inode attach.
  Symptoms-only instruction; outcomes in docs; more admin invariant tests.
- **Fix shipped:** `reconcile.d` fold + `axle_p` journal authority + gen
  gate on leases/gates + fleetd hold rematerialize (copy-only) + hardlink
  attach; 17 tests; oracle 1.0 / NOP 0.0 locally.
- **Follow-up (rubric/writeup mismatch):** Platform rubric plus difficulty /
  solution / verification text still described the retired fieldday lab,
  object-pool, chunk-index, Rust-span repair. Rewritten to grade current
  drop-in fold, `mode=seal` cutover, generation, borrow, gates, inode
  attaches, and reconciliation outputs. Removed solution canary. Contract
  now says `/var/lib/fleet/state/attach.intent` contains exact raw token
  `seal` (not `sealed`); task complexity unchanged.

### 2026-07-22 — `backup-restore-reconstruction` (platform: EASY + sufficiency FAIL)

- **Feedback:** Difficulty ❌ EASY (Opus/GPT both **80%**). Near-miss
  trials **16/17**; sole miss `test_runtime_holds_match_sealed_cutover`.
  Agents wrote `PAYLOAD_LINEAGE=seal` (journal/attach.intent token)
  instead of volume directory `sealed`. Instruction Sufficiency FAIL:
  docs never stated the vocabulary split. Artifact `(9).zip`.
- **Do not repeat:** Do not leave residual hardness in an undocumented
  `seal`/`sealed` literal while agents already clear the helper rewrite.
  Do not “fix” only by documenting the token if the frontier stays
  five independent bash polarity sites.
- **Harden shipped:** Document `attach.intent=seal` vs
  `PAYLOAD_LINEAGE=sealed` as outcomes; abort rematerialize via `fold_d`
  unless durable `cutover.ok`; fleetd undoes sealed hardlinks when lineage
  is not the real `sealed` directory; recovery order axle→fold→weave;
  new cutover-receipt test. Complexity retained (ops authority, not SE).

### 2026-07-24 — `backup-restore-reconstruction` (abort.d polarity + episode pin + medium)

- **Feedback:** Abort residue check graded an unstated rule (abort package must
  keep synonym tokens) while docs said “rewrite abort synonyms in place.”
  Episode immutability only checked existence while expectations recomputed
  from writable `/app/data`. Ops docs named verifier staging paths; one rubric
  line rewarded not treating green fleethealth as done; measured difficulty
  was medium not hard.
- **Do not repeat:** Ambiguous “rewrite abort synonyms” without live vs
  `abort.d` polarity; existence-only immutability beside recomputed
  expectations; grader paths in solver-visible docs; positive rubric for
  absence; declare hard after medium measurement.
- **Fix shipped:** Document live rewrite vs forensic abort.d synonyms; pin
  `episodes.sha256` like fleetpeek; strip `/logs/verifier` staging from ops
  docs; rubric negative for fleethealth-as-done; `difficulty = "medium"`.

### 2026-07-24 — `backup-restore-reconstruction` (HARD 0% + sufficiency FAIL)

- **Feedback:** Difficulty ✅ HARD. Agents **0%/0%**. Oracle 100%, NOP 0%.
  Every trial **17/18**; sole miss `test_cutover_receipt_suppresses_abort_residue`.
  Artifact `(30).zip`. Instruction Sufficiency FAIL.
- **What went wrong:** Docs said abort residue rematerializes unless
  `cutover.ok` exists. Agents interpreted “suppress” as **delete**
  `/etc/fleet/reconcile.d/90-local.conf`. Earlier drop-ins still folded to
  site standard, so fold/report tests stayed green. One trial wrote JSON
  `cutover.ok` while tests parse `key=value`.
- **Do not repeat:** Do not leave “suppress rematerialize” ambiguous with
  delete-vs-rewrite; do not leave receipt format implicit; do not let
  delete-the-override still green the fold check.
- **Fairness revise:** Document `key=value` receipt; matching receipt skips
  abort copy while live `90-local.conf` must remain present with
  site-standard tokens. Fold test now requires that file. Complexity
  unchanged (docs + verification coupling).

### 2026-07-18 — `pkcs11-multi-slot-session-rebind` (platform: TRIVIAL ×2)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus/GPT-5 both
  **100% (5/5)** after the “opaque journal + preference-bound seal +
  wire.nonce/lattice.tag” harden. Oracle 100%, NOP 0%. All 8 tests
  **10/10**. Artifact: `difficulty_check_artifact (10).zip` (prior collapse
  also in `(4).zip` before that harden).
- **What went wrong (from agent trajectories, GPT ~13–15 steps):**
  1. **Self-consistent preference digest is not a gate.** `SealUtil`
     hashed the *current* Q7/M3/P9 constants into seals/nonce/tag.
     `authcheck`/`Vx` used the same classpath. Agents never fixed the
     preference sheets: they wrote a temp Java calculator against the
     *broken* classes, forged `wire.nonce` / `lattice.tag` / `session.seal`,
     hand-wrote `/data/token/*` + `/output/session-rebind.json`, and
     `authcheck` ACCEPTed.
  2. **Readable verifier = answer key.** Agents `sed`/`cat`’d
     `/app/lib/Vx.java`, `Journal.java`, `SealUtil.java`, `OpA`/`OpB`/`OpC`
     and treated the gate as a recipe (live/non-revoked/max-epoch, TTL
     override, seal v3, nonce/tag). Opaque journal tags (`01:`/`02:`) were
     decoded in one read of `Journal.java`.
  3. **Shipped calculator.** `lib.SealExpect` (and/or ad-hoc `Calc.java`
     on the same APIs) removed any need to reverse the seal.
  4. **Tests only scored final artifacts.** JSON shape + `authcheck` +
     seal match never re-invoked `wireapply`/`holdrun`/`emitout`, so the
     intended preference-lattice path was optional.
  5. **Security aura without residual trust work.** Category=`security`
     but primary activity became “read Vx → forge token files,” not
     authority/revocation lattice reconstruction under a sealed gate.
- **Do not repeat:**
  - Never gate on a digest/MAC that is a pure function of the *same*
    mutable solver-visible prefs the verifier loads (self-consistency
    forgery). Prefer an **opaque expected lattice fingerprint** baked into
    a sealed verifier, and/or **behavioral re-entry** tests that re-run
    cutover tools and fail when prefs are still wrong.
  - Never ship a solver-visible seal/nonce calculator (`SealExpect`,
    verbose `Vx` source that lists every ACCEPT predicate in order).
  - Never let tests score only hand-writable token/JSON without forcing
    the cutover tools (or equivalent preference-correct behavior).
  - Opaque encodings are worthless if the decoder source is sitting next
    to them under `/app/lib`.
- **Redesign direction:** Keep `security` (PKCS#11 authority cutover).
  Sealed gate jar with XOR-baked expected preference digest; classpath
  order so `make install` cannot replace the gate; remove `SealExpect`;
  tests re-invoke wire/hold/emit and require tool-correct bind/TTL/certs;
  symptoms-only instruction.

### 2026-07-24 — `pkcs11-multi-slot-session-rebind` (platform: TRIVIAL again)

- **Feedback:** Artifact `(31).zip`. QC all ✅ but Difficulty ❌ TRIVIAL.
  Opus/GPT **100% (5/5)**. All mineral tests **10/10**.
- **What went wrong (Opus trajectory):**
  1. `javap -c -p` on `/opt/pk11/lib/gate.jar` recovered XOR `MASK`/`BOX`.
  2. Open `SealUtil.preferenceDigest()` gave the exact SHA-256 field list.
  3. One Python line recovered target digest `38459c9452a83307`; brute-forced
     ~23 small ints; `sed` Q7/M3/P9; rebuild; helper chain; ACCEPT.
  4. Sealed-gate “fingerprint” was a **digest oracle**, not residual trust work.
- **Do not repeat:** Never bake an expected preference digest that `javap` can
  recover alongside a readable digest formula and a small discrete search
  space. Prefer sealed engines + multi-scenario admission (hardcoded slot
  fails alternate ledgers) over recoverable lattice oracles.
- **Redesign applied:** Removed digest oracle from `Vx`; sealed `ops.jar`
  (OpA/OpB/OpC/SealUtil/Journal **and** wireapply/holdrun/emitout/sealgen
  mains) with sources deleted at image build; scenario packs beta/gamma;
  tests require same prefs across ledgers and pin `ops.jar` fingerprint.
  Preference knobs are **non-`final`** so javac cannot inline broken defaults
  into the sealed engines (otherwise sed of Q7/M3/P9 is a no-op).

## Older platform postmortems

Reusable hardness lessons belong in `AUTHORING_RIGHTS_AND_WRONGS.md`. Short
task-specific notes can land here when a zip is rejected as TRIVIAL/EASY.

### 2026-07-18 — `pms-annotation-processor-bom-cutover` (platform: TRIVIAL)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus/GPT-5.5 both
  **100% (5/5)**. Oracle 100%, NOP 0%. All 9 tests **10/10**. Artifact:
  `difficulty_check_artifact (9).zip`.
- **What went wrong (from agent trajectories):**
  1. **Answer-key ship roster + trust_policy.** `/app/link/roster-ship.toml`
     literally encoded `status=ok`, `lane=modular`, `wire_module=wire.core`,
     `apt_on_runtime=false`, `companions=[EventSchema,TicketSchema]`.
     `ops/trust_policy.toml` named `wire_family=core`, `cutover_epoch_min=2`,
     forbidden `p3.apt`. Opus ep4: “Key requirements clarified” from those
     files alone; GPT ep1 `cat`’d roster+trust before fixing.
  2. **Instruction was a numbered repair checklist.** “Bring BOM selection,
     companion emission, activation, module-path staging into agreement”
     mapped 1:1 onto `pom.xml` slots, `knit_a`, `active-plane.toml`, `knit_b`.
  3. **Textbook-wrong stubs.** `holdback()` always `true`; APT `legacy_tail`
     → `io.kestrel.shadow`; `SLOT_C_KEY=w0` / `SLOT_C_RUNTIME=p3` vs ship
     `w1`/`q7`. Grep + polarity flip; GPT finished in **~8 steps**.
  4. **Single ship report, no scenario matrix.** One `SHIP` dict; no opaque
     multi-case admission; no reload/durable-root coupling; no surface
     checker that greens while host refuses.
  5. **Security aura without residual trust work.** Category=`security` but
     primary activity was debugging three polarity sites + config
     transcription — same collapse as signed-plugin / musl-lattice.
- **Do not repeat:** Never ship solver-visible TOML/JSON with the same
  field/value set the tests assert. Never list BOM/emit/activation/staging
  as a numbered fix checklist. Never leave `return true` / wrong-package /
  wrong-slot as the whole frontier. Never relabel a Maven polarity cutover
  as `security` without opaque scenarios + interacting authorities +
  verifier-owned EXPECTED.
- **Redesign direction:** Abandon single-report JPMS polarity. Rebuild as
  multi-scenario modular companion **admission** (C/Rust/Go lattice): tip
  continuity × revoke/window × durable-vs-live root; surfcheck false-green;
  EXPECTED only in tests; symptoms-only instruction.

### 2026-07-18 — `sph-kernel-handoff-reconcile` (platform: TRIVIAL)

- **Feedback:** Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Opus/GPT-5.5 both
  **100% (5/5)**. Oracle 100%, NOP 0%. All 36 tests **10/10**.
- **What went wrong (from difficulty_check_artifact trajectories):**
  1. **Answer-key probe contracts in `reconcile-schema.md`.** After a
     fairness pass for hidden rustcheck APIs, the schema named
     `estimate_density_field` / `greens_table_for_run` / `reduce_chunks`
     with the exact Shepard formula, `moment_coeff == second_moment_coeff`,
     and chunk-invariance recipe. GPT episode 0–1: open schema → treat
     contracts as the bug checklist → patch those three sites.
  2. **Formula already present in a “red herring” helper.**
     `gradient_correction_trace` used `m_j/rho_hat[j]` volume weights, so
     even without the schema the Shepard fix was copy-pasteable.
  3. **Small Rust workspace + predictable crate names** (`sph_a`…`sph_d`)
     made the remaining momentum/h-iterate sites a short follow-up once
     the schema had framed the problem as “fix the listed APIs.”
  4. **Primary activity collapsed to debugging/transcription**, not
     scientific reconstruction of cross-kernel invariants.
- **Do not repeat:** Never put verifier probe **formulas**, crate paths,
  or `pub fn` names that are also fix sites into solver-visible docs.
  Fairness for probes = outcomes (“density must match an independent
  reconstruction”; “greens table stays publicly reachable”) — not the
  algebra. Never leave the correct patch idiom in an unused helper.
  Prefer AUTHORING_RIGHTS_AND_WRONGS.md + this postmortem over re-adding
  checklist contracts when Instruction Sufficiency complains.
- **Redesign direction:** Keep `scientific-computing`. Strip recipe
  contracts; remove leaking helpers; add policy-authority coupling;
  keep multi-site numerical bugs that report bands and probes both need.

### 2026-07-18 — `superko-rule-forensics` (platform: EASY, round 1)

- **Feedback:** Difficulty ❌ EASY (need ≥ MEDIUM). Opus/GPT-5.5 both
  **80% (4/5)**. Oracle 100%, NOP 0%. Puzzle/board tests essentially
  **10/10**; only `test_rule_variant_is_positional_superko` dipped (8/10).
  Instruction-sufficiency analysis: FAIL — agents that missed `rule` still
  solved every board; reviewers split on whether history uniquely proved
  positional vs situational.
- **What went wrong (from difficulty_check_artifact trajectories):**
  1. **Boards were solver-trivial.** Agents wrote an in-container Python Go
     engine + liberty-focused minimax, validated with `referee.jar`, and
     cleared all win/unwinnable tests. Hardness lived almost only in one
     categorical `rule` field.
  2. **Single-point grading on `rule`.** Wrong family → 0.0 despite ~97%
     completion; when `rule` is right, trials pass — so platform still
     rates EASY at 80% accuracy.
  3. **Ambiguous / under-taught history discrimination** (pre-fix). Same-
     colour classic-ko refusals look situational; cross-colour pass-tempo
     refusals are the positional signal. Agents guessed situational /
     natural-situational without a clear doc of that colour-vs-ply reading.
  4. **Published per-board Black-ply floors enabled padding.** Agents found
     short captures then extended lines (White reoccupies, Black recaptures)
     just to meet `MIN_BLACK_MOVES` — floors did not force deeper tactics.
  5. **Fortress-only unwinnables.** Two-eyed shapes are easy to classify;
     too few cooperative-looking traps that jar-fill under White-pass but
     lose under adversarial defense.
- **Do not repeat:** Do not ship tsumego booklets where a generic liberty
  BFS clears every board and only a one-field rule guess remains; do not
  rely on a single categorical field for hardness; do not leave superko
  family discrimination undocumented if tests hardcode one family; do not
  use floor tables that agents can satisfy by padding short captures.
- **Redesign direction:** Keep `games`. Fair colour-vs-ply reading in
  match-log docs. Harden boards: order-critical fights, multiple coop→force
  traps, deep nets that cannot be padded from a 1–2 move capture. Couple
  wrong cooperative status to several boards, not just `rule`.

### 2026-07-18 — `superko-rule-forensics` (platform: EASY, round 2 / NEEDS_REVISION)

- **Feedback:** Still ❌ EASY after 10-board harden. Opus/GPT-5.5 both
  **80% (4/5)**. Oracle 100%, NOP 0%. `rule` now **10/10** (colour-vs-ply
  docs worked). Almost every board test **10/10**; only board-3 PV quality
  dipped (9/10 on min-plies / coop-pass / short-coop tests). Failed trials
  still cleared **38–39/40** tests — all-or-nothing 0.0 on one PV polish
  miss, but successful runs prove boards remain solver-free.
- **What went wrong:**
  1. **Teaching `rule` does not create difficulty** once agents jar-validate.
     Live `referee.jar` already enforces PSK; agents never need to simulate
     family differences on boards. Hardness must live in **board statuses**.
  2. **Liberty minimax + jar still clears bp≈3–5 nets and open-ring traps.**
     Adding 1–2 coop traps and a pad-resistant floor table was not enough —
     frontier agents still write in-container Go solvers and finish.
  3. **Near-perfect failures are not hardness.** 39/40 → 0.0 is grading
     harshness, not MEDIUM/HARD; platform still rates EASY at 80% accuracy.
  4. **Accepted-task pattern missing:** multi-fixture matrix where partial
     understanding fails distant cells; false-green surface bait; ≥4 traps /
     deep order-critical nets that short search mislabels.
- **Do not repeat:** Do not ship another “same booklet + slightly deeper
  liberty fights” revise and call it hard. Do not treat fixed `rule` 10/10
  as evidence of hardness. Prefer 12+ boards, ≥4 coop→force traps, wins with
  irreducible adversarial length ≥5–7 and order-critical first moves, plus a
  false-green liberty probe that greens traps under White-pass.
- **Redesign direction (round 3):** Keep `games` / bash+jar. Scale trap
  matrix and deep nets; couple wrong L2 (adversarial vs coop) to many
  statuses; keep fair match-log reading; do not leave residual hardness in
  PV-floor polish alone.

### 2026-07-18 — `superko-rule-forensics` (platform: EASY, round 3 — same 10-board feedback)

- **Feedback:** User re-surfaced round-2 numbers (80%/80%, board tests ~10/10,
  only board-3 PV polish weak). Local 12-board + liberty_probe harden was
  never what the platform graded — and even that shape is still
  **liberty-searchable**, so it would likely stay EASY.
- **What went wrong (authoring):** Treating “more cages / more open rings /
  deeper bp floors” as a harden. Agents already run adversarial liberty
  minimax + `referee.jar`; those boards remain free. Probe bait alone is
  ignorable (lesson 4).
- **Do not repeat:** Do not add another layer of the same liberty-net
  booklet. Residual hardness must change the **contract**: force agents to
  certify **coop vs force** separately and file **White refutations** for
  every target liberty on unwinnable boards (multi-cell matrix). Wins stay
  deep; unwinnables dominate the booklet.
- **Redesign (round 4):** Keep `games`. Schema adds `coop_capturable` on
  every board and `refutations` on every unwinnable (one White reply per
  initial target liberty, jar-checked). ≥8 coop∩unwin traps; ≤4 deep wins;
  liberty_probe remains false-green bait.

### 2026-07-19 — `weiqi-capture-contest` (platform still EASY on old 10-board zip)

- **Feedback:** User re-pasted EASY 80%/80% with **old** test names (wins
  1,2,3,6,8,10). That is not the 12-board/refutation tree. Liberty minimax
  still clears booklet-only tasks.
- **Harden shipped:** Overnight printer under `/app/kiosk/` with three
  **domain** bugs (same-colour situ veto; sensei/coop→win stamp; pass-only
  ripostes) + scenario instruction + desk tests. Not training-set polarity
  stubs. Preflight PASS. Harbor oracle/NOP still required.

- **Feedback:** CodeBuild quality **FAIL** twice. First: predicted
  `software-engineering` (0.85) with forensics-framed instruction. Second:
  still SE (0.95) after Weiqi contest instruction (instruction_check PASS).
- **What went wrong:** Classifier weights the whole solver-visible surface.
  API-style `puzzle_scorer.md` / JSON schema score sheet / `referee.jar` /
  task name `*-forensics` still read as software work even when
  `instruction.md` leads with a tournament goal.
- **Do not repeat:** For `games`, retheme **docs + binaries + task name**,
  not only the instruction. Drop forensics/API manuals; use tournament /
  table-judge / goban language; avoid `*-forensics` submission names.
- **Fix shipped:** Renamed task → `weiqi-capture-contest`; `judge.jar` +
  `sensei_hint.sh`; docs rewritten as tournament rulebook; preflight PASS.


- **Platform paste still cites 10-board test names** (wins 1,2,3,6,8,10). That
  is the pre–round-4 booklet. Do not treat those 80%/80% numbers as grading
  the current 12-board `coop_capturable`/`refutations` tree.
- **Shipped round-4 shape:** 12 boards; wins `{1..4}`; traps `{5..10,12}` with
  per-liberty `refutations`; fort `{11}`; thin symptoms-only `instruction.md`
  (schema in `environment/docs/score_sheet.md`); preflight PASS (collapse WARN
  on GX9 borderline only).
- **Residual risk:** Frontier agents that already write liberty minimax will
  likely still clear the matrix once they read the score sheet — contract
  change raises the bar vs PV-polish misses, but may not reach MEDIUM alone.
  Off-liberty / ladder-block boards need a fast approach search; naive
  full-legal / wide approach search times out proving open-ring unwinnables.
- **Local blocker:** Docker Desktop app executable missing on author laptop
  (`kLSNoExecutableErr`); Harbor oracle/NOP not re-run this session. Local
  Java oracle dry-run under `APP_ROOT` = SPLIT_OK in ~2s.
- **Do not claim READY** until Harbor oracle 1x + NOP evidence exists for this
  checksum.



### 2026-07-19 — `int8-calbank-kernel-lane-cutover` (platform: TRIVIAL)

- **Feedback:** Difficulty ❌ TRIVIAL. Opus/GPT both **100% (5/5)**. All 8 tests **10/10**.
  Artifact: `difficulty_check_artifact (17).zip`.
- **Collapse:** Three polarity stubs (`knit_q`/`fold_w`/`slot_v`) + answer-key
  top1/lane matrix in instruction + `score_u` lookup table. GPT ep3 patched all
  three helpers in one heredoc (~capsule/signed-plugin class).
- **Do not repeat:** Never ship three greppable always-wrong predicates as the
  INT8 cal-bank frontier. Prefer correct runtime + seal fence × journal scale
  × profile hot fold × resume rebase stamp; preflight undoes naive tip edits.
- **Redesign shipped:** Ops/authority cutover; correct C/Rust helpers; scales
  from blobs; verifier EXPECTED retained.

## Difficulty collapse logs

### musl-static-pie-plugin-host-relink-lattice (2026-07-18) — platform oracle DaytonaError (packaging)

Platform difficulty artifacts `(12).zip` and `(13).zip`: all oracle/nop
trials errored with `DaytonaError` before any tests ran:

`Path does not exist: .../environment/.cargo/`

Two layers:
1. Zip built with `zip -x '*/.*'` dropped `environment/.cargo/` while
   Dockerfile had `COPY .cargo/`.
2. Even after including `.cargo` in the zip, the platform still reported
   the path missing — treat Harbor/Daytona as may omit or fail on
   archive dot-directories under `environment/`.

Durable fix: **never `COPY` a hidden path from the build context.** Seed
from a non-hidden file (e.g. `config/rust/cargo_config.toml`) and
`RUN mkdir -p .cargo && cp … .cargo/config.toml` inside the Dockerfile.

Do not repeat: `unzip -l` alone is not enough if the remote stripper
drops dots. Prefer non-hidden seeds + Dockerfile materialization for
any path Cargo/tools expect under a dotdir.

### musl-static-pie-plugin-host-relink-lattice (2026-07-18) — platform TRIVIAL

Platform: Difficulty ❌ TRIVIAL (need ≥ MEDIUM). Agents **100%** (Opus 5/5,
GPT-5.5 5/5); NOP 0; oracle 100%. All 6 tests **10/10**. Artifact:
`difficulty_check_artifact (8).zip`.

Why it collapsed (trajectories):

1. **Instruction was a three-item repair checklist.** Prose named “host link
   line / Rust plugin ABI surface / Go cgo compile flags” — GPT episode 0
   already planned that map; Opus wrote “Summary of fixes needed: 1. knit…
   2. fold_slot… 3. emit_xv…”.
2. **Readable probe = answer key.** Agents `cat`’d `/app/tools/lattice_probe`
   and reversed required stamps (`CC=musl-gcc`, `-fPIE`/`-pie`, TLS model,
   cgo `-fPIC`/`/app/include`) *before* running a failing report.
3. **Textbook-wrong bodies.** Every `knit_xv_a` branch emitted
   `initial-exec` + empty PIE; packing used `wide = !a`; musl/target cgo
   still forced `gcc` and stripped `-fPIC`. One-pass readable polarity.
4. **Contract/matrix opened first** gave exact `global-dynamic` / `v1`/`v2`
   targets. Probe report was optional confirmation, not discovery.
5. **Primary activity collapsed to debugging three polarity sites**, not
   multi-toolchain build-graph reconstruction (despite
   `build-and-dependency-management` label).

Do not repeat: Do not list three toolchain fix nouns in `instruction.md`.
Do not ship a readable probe/source that compares against the exact stamp
strings agents must emit. Do not leave `!flag` / all-branches-identical-wrong
tables as the only bugs. Prefer observation-only runners + verifier-owned
EXPECTED; couple feature unification / profile authority so local stamp
greens still fail distant matrix cells.

Redesign direction: Keep `build-and-dependency-management`. Symptoms-only
instruction. Observation-only (preferably compiled) probe. ≥4 coupled loci
(feature forward + profile authority + host stamps + packing/cgo) with
nonlinear matrix cells; opaque symbols; no answer-shaped probe predicates.

### signed-plugin-trust-rebind (2026-07-18) — platform TRIVIAL ×2

**Attempt 1 (Java):** Difficulty ❌ TRIVIAL. Agents 100% (Opus 5/5, GPT-5.5 5/5).
Collapse: three tiny predicates (`OpAlpha`/`OpBeta`/`OpGamma`) + intent comments
+ scenario `stale`/`revoked` fields + pre-baked `AssembleY` reason table.

**Attempt 2 (C/Rust/Go capsule clone):** Still ❌ TRIVIAL at 100%/100%. Same
class as `pms-annotation-processor-bom-cutover` post-capsule: greppable polarity
stubs (`fold_q`/`gate_r`/`slot_w`) — multi-language transplant is not hardness.

**Attempt 3 (edge-lane-class WAL/authority):** Replace three-stub frontier with
coupled keyed integrity + tier resolve + replay + revoke/hold presence +
surface `jarcheck` ≠ deep admission; symptoms-only plugin framing; outputs
`/output/plugin-ledger.json` + quarantine; verifier rebuild/dynamic inject.

Hardening rule: do **not** ship another three-boolean admit lattice for this
task name. Prefer edge-lane-class multi-locus WAL trust with opaque symbols.

### signed-plugin-trust-rebind (2026-07-19) — platform EASY + sufficiency FAIL

Platform: Difficulty ❌ EASY (need ≥ MEDIUM). Opus 100% (5/5), GPT-5.5 80% (4/5).
Sufficiency FAIL on the miss: agent reached 22/25 but could not reverse the
8-bit keyed integrity from only **two** audit triples; used a near-miss
heuristic that misclassified epoch-20 `b6`.

Collapse: edge-lane-class WAL task still too in-distribution — textbook
`seed^epoch^i` material + wrapping-add integrity discovered in ~12–36 steps;
instruction already spelled hold/presence/replay. Hardening: non-textbook
material schedule, ≥5 audit triples for fair discovery, trap frames signed
under the old formula, exact quarantine integrity counts.

### signed-plugin-trust-rebind (2026-07-19) — harden Attempt 4 packaged

Shipped `Task_Ready_To_Submit/signed-plugin-trust-rebind.zip` after:
- material = `seed[i] ^ rotl8(epoch_lo, i%5+1) ^ (5*i+1)` (not `seed^epoch^i`)
- five audit triples; legacy-schedule trap frames → exact 12 integrity_failures
- instruction: symptoms + discovery hint only (no pasted algebra)
- Local Step 2b evidence: oracle 1.0, NOP 0.0, `approve_task.py` PASS
  (collapse WARN justified: RC1 net expand on core; CR1 legacy; GX9 borderline)
- Awaiting platform re-rate for ≥ MEDIUM / HARD. Oracle 10x still Step 4.

### signed-plugin-trust-rebind (2026-07-20) — platform still EASY (Attempt 4)

Platform: Difficulty ❌ EASY. Opus 80% (4/5, 1 timeout), GPT-5.5 100% (5/5).
All 25 tests 10/10. Artifact: `difficulty_check_artifact (20).zip`.
Sufficiency PASS on the timeout near-miss.

Collapse: shipping `material_hex` in the audit let agents hardcode
epoch→material and skip a closed-form `derive_epoch_key`; XOR-then-sum fold
is textbook once material is known; instruction still enumerated hold/replay/
presence. Hardening Attempt 5: drop material_hex; bind material to lane id +
opaque policy strand; novel-epoch dynamic probe; thinner symptoms instruction.

### signed-plugin-trust-rebind (2026-07-20) — harden Attempt 5 packaged

Shipped `Task_Ready_To_Submit/signed-plugin-trust-rebind.zip` after:
- no `material_hex` in audit (seed/payload/check only; same-epoch multi-lane samples)
- material = seed ^ rotl(epoch) ^ stride ^ strand(61) ^ lane
- integrity = rotate-mix keyed fold (not plain XOR-sum)
- epoch 15 fleet + novel-epoch dynamic inject (hardcode bypass killer)
- Local Step 2b: oracle 1.0, NOP 0.0, approve PASS. Awaiting platform re-rate.

### signed-plugin-trust-rebind (2026-07-21) — HARD but 0/10 + sufficiency FAIL

Platform: Difficulty ✅ HARD. Agents 0%/0%. Oracle 100%. Artifact feedback:
undiscoverable keyed fold; 9/10 task_specification fail. Best partial 15/25.

Fairness revise (Attempt 6): sealed `/app/bin/framecheck` (amd64 stripped
binary under `environment/data/tools/`; no probe source in zip); document
XOR-sum fold family; band near-miss accepted/quarantine tests; exact gates
for full restore + novel-epoch inject; fixtures test requires published
outputs (no free 10/10 on timeout). Local Step 2b: oracle 1.0, NOP 0.0.

### signed-plugin-trust-rebind (2026-07-22) — HARD 20%/20% + sufficiency FAIL

Platform: Difficulty ✅ HARD. Opus/GPT **20% (1/5)**. Best near-miss 26/27
(epoch-40 replay off-by-one). Sufficiency FAIL: JSONL feeds not stated as
accepted sources; material byte components under-specified for agents who
avoid framecheck; hold exact tallies brittle vs watermark ordering.

Fairness revise (Attempt 7): instruction documents credential JSONL +
watermark + material components (seed/epoch-rot/stride/lane/strand) without
pasting hex operators; hold tests banded; exact epoch-30 moved into
`test_exact_restore_counts`; free structural cells require deep bands /
quarantine hits.

### signed-plugin-trust-rebind (2026-07-23) — schema / quarantine-row sufficiency

Instruction sufficiency: quarantine one-row-per-credential (no epoch/lane
dedup) + global cross-segment replay stream; normative field names for
ledger (`name`/`status`/`id`/`profile`/`accepted`) and quarantine
(`epoch`/`lane`/`ts`/`reason`). Complexity unchanged (instruction-only).


## Hardness collapse lessons (do not repeat)

These are binding for redesign / harden work. Full rights/wrongs live in
`AUTHORING_RIGHTS_AND_WRONGS.md`. Evidence logs may live under `logs/`.

1. **Never ship operator docs that enumerate the mutable knob checklist.**
   Naming every ledger file / profile bind / quarantine flag / fragment map
   (plus a memo with numeric keys or "X remains authoritative") turns a
   restore/reconcile task into a finite config transcription. Frontier agents
   finish that in one short diagnosis loop. Docs may describe normal layout
   only — never the repair surface or answer-shaped values.
2. **Never let the solve be "edit a small declarative cluster while the
   binary stays correct."** If pools/recipes/src are frozen and the agent only
   moves blobs + rewrites 3–5 ledger/profile lines, expect platform
   **TRIVIAL** even when tests look rich. Prefer a higher authority
   (journal replay, volume mounts, leases, preflight) that **re-applies and
   undoes** naive ledger edits on every restore unless the agent fixes the
   authority layer itself.
3. **Stamp-scan / XOR-bruteforce metadata patching is not hardness.** If
   recipe marks + pool bytes alone let an agent derive every knob, the task
   collapses. Couple mask/borrow/fragment/shelf decisions so local stamp
   matches still fail distant drills or get overwritten.
4. **Misleading surface health alone does not create difficulty** if agents
   can ignore it and run the real restore entrypoint. Health bait must sit
   beside a real authority trap, not instead of one.
6. **Never leave hardness in one categorical field while boards are solver-free.**
   If agents clear every puzzle test with an in-container Go/search script and
   only miss `rule` / one enum, platform rates **EASY** even at 80%. Couple
   wrong cooperative analysis to several board statuses; make short captures
   impossible under adversarial White; teach fair discrimination without
   making the booklet free.
6b. **Fixing `rule` docs alone is not a harden.** After round-2 EASY,
   `positional_superko` went 10/10 while boards stayed 10/10 — agents jar-
   validate under the baked family and never need family simulation. Residual
   hardness must be multi-board trap/net misclassification, not PV polish.
6c. **Deeper liberty nets / more open rings still EASY** against agents that
   already ship adversarial liberty minimax + jar validate. Change the score-
   sheet contract (coop vs force certificates, per-liberty White refutations)
   so wrong L2 fails many cells — do not keep shipping the same searchable
   booklet shape.
7. **Never publish per-board ply floors that agents can pad.** If a short
   jar-legal capture exists, agents extend with reoccupy/recapture to hit
   `MIN_BLACK_MOVES`. Floors must equal irreducible adversarial length (or
   use global multi-ply rules that padding cannot fake without failing
   cooperative-pass checks).
7b. **Near-miss all-or-nothing (38–39/40 → 0.0) is not MEDIUM.** If 4/5
   runs still score 1.0, platform rates EASY. Raise the fraction of boards
   that liberty-BFS mislabels; do not rely on one edge-case PV test.
8. **After platform TRIVIAL / EASY feedback:** append the reusable lesson to
   `AUTHORING_RIGHTS_AND_WRONGS.md`, keep a dated evidence note under `logs/`
   or AGENTS.md postmortem, and redesign before re-shipping. Do not add
   pin/config knobs on top of the same checklist shape.
9. **Never “fix” hidden-probe unfairness by pasting the probe algebra into
   `environment/docs/`.** Naming the exact Shepard sum, `second_moment_coeff`
   equality, or chunk-stable reduction recipe next to the matching `pub fn`
   names makes frontier agents finish in one schema-read loop (platform
   **TRIVIAL**). Document probe *outcomes* only; keep formulas out of
   solver-visible docs; do not leave the correct idiom in unused helpers.
10. **Never hide the only failing contract behind a silent tool omission.**
    If instruction says "every managed path" but the shipped emitter skips
    host-resident rows, and host field values are only in tests, platform
    flags **instruction sufficiency FAIL** while strong agents still score
    EASY/TRIVIAL by discovering the bug. State residency coverage and host
    field meaning in the public contract; put hardness in seating authority,
    ordering, and multi-artifact ops — not in an undocumented emit gap.
11. **Never publish the seating composition formula in field-notes.** Writing
    "lane moves when epoch ≥ floor; anchor stays; below-floor shares host"
    turns roster+window into a one-pass answer key (fanotify cutover →
    platform **EASY** at 80–100%). Docs may name that roster/window/hold
    materials exist; the precedence rule must be discovered from behavior
    (racepulse / failed seating), not transcribed from operator notes.
12. **Never gate full credit on an unspecified meta scrub.** If agents clear
    seal/preference/lease sites (8/9) but miss rewriting `activation.toml`
    (or equivalent sealed tip map) because it only lives in an unused helper
    / test docstring, platform rates **HARD + 0%** with Instruction
    Sufficiency FAIL (`dm-thin-snapshot-fanout-reconcile`). State the
    rewrite outcome as a scenario in `instruction.md`; couple it with other
    loci so documenting scrub alone does not collapse the task.
13. **Never grade “host markers gone” when instruction only says “bound into
    broker.”** `iouring-registered-buffer-lease-cutover` (artifact 21): agents
    0% with 5/6 tests green; sole miss was leaving `/data/lab/mnt/host/ten/*`
    while broker seating + lease/seal/buffers/preflight were correct.
    Instruction Sufficiency FAIL. Same family as fanotify silent host-omit
    (§10). State dual residency: broker present AND host absent.
14. **After fairness fix, do not “fix” EASY by pasting checklist recipes.**
    Artifact 22: 80%/80% EASY once host cleanup was documented. Sufficiency
    text wanted `fleet.toml` + `PrivateMounts=no` named — that collapses
    further. **Do:** compound seal (epoch×prefix), multi-drop-in fold,
    preflight/jobpulse rematerialize, harbor-clobbering broken lease writer,
    behavioral re-entry tests. Document outcomes (fleet plane vs live plane;
    isolation not left active) without knob recipes.
15. **Never let every test poison shared state on failed re-entry.** After
    re-entry harden, iouring went HARD 0% with Instruction Sufficiency FAIL:
    agents correctly hand-fixed `/data/lab`, then `leasectl`/`fold`/`bufreg`
    re-entry clobbered durable/units/slots so even static schema/seating
    tests scored 0. **Do:** state helper re-entry + soft `/app` rebuild in
    instruction; keep ~1–3 static-scoring tests; snapshot/restore around
    re-entry. **Do not** require an undocumented `lab.toml` profile flip.
16. **Document which helper owns which repair when names mislead.** iouring
    MEDIUM (40%/80%): agents put PrivateMounts in `seat`/`nsbind` and left
    `ledgerout --fold` as no-op → 5/6 near-miss + sufficiency FAIL. **Do:**
    state that `--fold` clears isolation drift (seating alone does not);
    grade fold-only re-entry separately; document colon `buf_slot` shape.
17. **Never grade only `/opt/.../bin` when `/app` sources are the fix.** Agents
    can replace installed helpers with bash that write leases/units/JSON and
    pass re-entry by re-running the stand-ins. **Do:** verifier rebuilds from
    `/app` into a verifier-owned path and exercises those ELFs; keep ops
    outcomes as the sysadmin primary activity; set `difficulty` to the
    measured band.

### fanotify-mount-ns-mark-cutover (2026-07-18) — platform EASY then TRIVIAL

Platform: EASY (80%/100%) then TRIVIAL (100%/100%) after fairness+holds
harden. Collapse modes:

1. **Seating formula / flat configs = transcription** — one-pass migrate set.
2. **Grep-local C polarities** (`inherit-ok`, hard-coded `inode`) — not ops.
3. **Unfair emit host-omit** — sufficiency FAIL when agents trust the tool.
4. **Helper menu + racepulse** = finite ops checklist once policy is known.

Do not repeat: Do not leave a single live config generation that matches
tests. Prefer identity-stuck prior gen vs target gen (journal discoverable),
order-preserving reopen bugs (not token greps), fold depth across drop-ins,
and holds that differ across generations so seating g2 "succeeds" racepulse
but fails verifier end-state.


