# Idea Proposals — 2026-07-25

Open categories only (repo taxonomy): `games`, `machine-learning`, `system-administration`.
Blocked categories from the pasted six-way form (`Build / Compilation…`, `Security…`, `Scientific Computing`) are **not used**.

Coverage: 4 × System / Environment Setup & Configuration · 3 × Machine Learning / Model Training / Inference · 3 × Interactive / Simulation Tasks / Games.

---

## 1. Autofs Multi-Map Seating Cutover

**Idea Category:** System / Environment Setup & Configuration

Task Idea Summary:
```
Bring the live automounter desk under /etc/auto.master.d/, /etc/autofs/, and /var/lib/autofs/ into agreement with the durable map authority so that `/app/ops/run_autofs_seat.sh` produces `/output/autofs-seat.json` with fields schema_tag (string), maps (array of {name:string, mountpoint:string, generation:integer, source:string, active:boolean}), holds (array of {key:string, until_epoch:integer}), and seating_ok (boolean). Surface tool `/usr/local/bin/autofshealth` may print OK while deep seating is wrong. Frozen fixtures under /app/data/maps/ are integrity-pinned; do not rewrite them. A map is active only when its generation is at or above the durable floor, its hold window (if any) has not expired, and drop-ins under /etc/auto.master.d/ fold in lexical order without a later abort override. Running the seating entrypoint twice must yield byte-identical /output/autofs-seat.json.
```

Associated Skills:
```
autofs map seating; drop-in fold order; generation floors; hold windows; ops entrypoint idempotence; live /etc and /var reconciliation; surface-health vs deep seating; JSON seating ledgers
```

Task Tags:
```
autofs, map-seating, dropin-policy, generation-gate, ops-journal, hold-window
```

- **Why this category is correct:** Primary work is configuring live automount end-state via ops entrypoints on `/etc` and `/var`, not rewriting application logic or hunting a single bug.
- **Why the Task is Difficult:** Drop-in fold × generation floor × hold expiry × abort override couple so greening autofshealth or one map file still fails distant cells.
- **Hidden Reasoning Challenges:** Which authority wins when live tip, durable floor, and abort.d disagree; whether expired holds leave stale mounts published; lexical fold vs “last file wins” bait.
- **Why This Idea is Original:** Distinct from `nfs-delegation-copy-reconcile` (NFS grace/delegation), `backup-restore-reconstruction` (fleet volumes), and `iouring-registered-buffer-lease-cutover` (buffer leases). Autofs multi-map seating is not in the shipped set.

---

## 2. Libvirt Pool Attach and Disk Seating

**Idea Category:** System / Environment Setup & Configuration

Task Idea Summary:
```
Seat virtual-machine storage so `/app/ops/run_pool_attach.sh` writes `/output/libvirt-attach.json` with fields schema_tag (string), pools (array of {name:string, path:string, uuid:string, state:string}), disks (array of {domain:string, target:string, source:string, pool:string, attached:boolean}), and attach_ok (boolean). Live materials live under /etc/libvirt/storage/, /etc/libvirt/qemu/, and /var/lib/libvirt/; durable authority and hold receipts live under /var/lib/libvirt/ops/. A disk is attached only when its pool is active, the domain definition references the durable pool UUID (not the surface decoy), and a matching key=value cutover receipt exists. `/usr/local/bin/virthealth` may report healthy while attach_ok is false. Fixtures under /app/data/pools/ are frozen. Two consecutive runs of the attach entrypoint must produce byte-identical /output/libvirt-attach.json.
```

Associated Skills:
```
libvirt storage pools; domain disk attach; UUID authority; cutover receipts; live /etc/libvirt seating; ops rematerialize; surface health bait; idempotent attach reports
```

Task Tags:
```
libvirt, storage-pool, disk-attach, cutover-receipt, ops-journal, uuid-authority
```

- **Why this category is correct:** Solver operates live libvirt admin surfaces and an ops attach entrypoint; language of helpers is incidental.
- **Why the Task is Difficult:** Pool state, domain XML source paths, UUID preference, and receipt format must all agree; deleting the override to “suppress rematerialize” fails fold-style checks.
- **Hidden Reasoning Challenges:** Surface pool path vs durable UUID; receipt `key=value` vs JSON bait; rematerialize that rewrites naive domain edits unless receipt matches.
- **Why This Idea is Original:** Not a clone of `block-volume-crash-reconcile`, `dm-thin-snapshot-fanout-reconcile`, or `overlay-image-layer-reconciliation` — those are block/thin/overlay, not libvirt pool+domain seating.

---

## 3. Chrony Stratum Preference Lattice

**Idea Category:** System / Environment Setup & Configuration

Task Idea Summary:
```
Configure the time desk so `/app/ops/run_time_seat.sh` emits `/output/time-seat.json` containing schema_tag (string), sources (array of {name:string, stratum:integer, selected:boolean, hold:boolean}), preference (string: live|durable|authority), sync_ok (boolean), and offset_bound_ms (number). Live chrony/timesync materials sit under /etc/chrony/, /etc/systemd/timesyncd.conf.d/, and /var/lib/chrony/; durable preference under /var/lib/time/ops/prefer.toml. A source is selected only when it is present in the durable roster, its stratum is within the published band documented under /app/docs/time_bands.md, and it is not held. `/usr/local/bin/timehealth` may print synchronized while sync_ok is false. Do not rewrite frozen samples under /app/data/sources/. Running the seating entrypoint twice must yield byte-identical output.
```

Associated Skills:
```
chrony source seating; stratum bands; preference lattices; systemd timesync drop-ins; hold flags; ops entrypoint rebuild; live time-state reconciliation; idempotent JSON reports
```

Task Tags:
```
chrony, stratum, time-seating, preference-lattice, dropin-policy, hold-window
```

- **Why this category is correct:** End-state is live time-service configuration and seating reports via ops scripts — classic system administration.
- **Why the Task is Difficult:** Prefer.toml rematerializes live sources unless durable; stratum band × hold × roster couple; surface sync ≠ selected durable source.
- **Hidden Reasoning Challenges:** Which drop-in wins; hold vs omit; offset_bound_ms derived from seated source not from timehealth’s optimistic reading.
- **Why This Idea is Original:** No existing task centers chrony/timesync preference seating; distinct from systemd unit cascade and NFS/reboot recovery.

---

## 4. HAProxy Runtime Drain and Backend Seating

**Idea Category:** System / Environment Setup & Configuration

Task Idea Summary:
```
Seat reverse-proxy backends so `/app/ops/run_proxy_seat.sh` produces `/output/proxy-seat.json` with schema_tag (string), backends (array of {name:string, server:string, weight:integer, drained:boolean, generation:integer}), socket_applied (boolean), and seat_ok (boolean). Live config lives under /etc/haproxy/ and /etc/haproxy/conf.d/; runtime socket state and leases under /var/lib/haproxy/ and /var/run/haproxy/. A server is in service only when its generation meets the durable floor, it is not drained, and the runtime socket apply matches the folded conf.d weights. `/usr/local/bin/proxyhealth` may show UP while seat_ok is false. Fixtures under /app/data/backends/ are integrity-pinned. Two runs of the seating entrypoint must be byte-identical on /output/proxy-seat.json.
```

Associated Skills:
```
haproxy conf.d fold; runtime socket apply; backend drain; generation floors; weight seating; ops idempotence; surface UP vs deep seat; /etc and /var proxy state
```

Task Tags:
```
haproxy, backend-seating, runtime-socket, drain-window, generation-gate, conf-fold
```

- **Why this category is correct:** Primary activity is operating live proxy admin state (config fold + runtime socket + leases), not implementing a load balancer.
- **Why the Task is Difficult:** File fold, socket apply, drain lease, and generation must cohere; editing only haproxy.cfg leaves conf.d abort residual.
- **Hidden Reasoning Challenges:** Drain vs weight-zero; socket_applied false when files look right; rematerialize undoes naive weight edits without durable receipt.
- **Why This Idea is Original:** Distinct from `systemd-unit-cascade-rollback` and fleet restore tasks; no HAProxy runtime-drain seating task in the repo.

---

## 5. Embedding Bank Temperature Recalibration

**Idea Category:** Machine Learning / Model Training / Inference

Task Idea Summary:
```
Bring the contrastive embedding evaluation engine under /app/eng into agreement with documented metric bands so `/app/scripts/run_embed_eval.sh` writes `/output/embed-eval.json` with schema_tag (string), scenarios (array of {id:string, recall_at_10:number, nmi:number, temperature:number, bank_epoch:integer}), and bands_ok (boolean). Frozen banks and checkpoints live under /app/data/banks/ and /app/data/checkpoints/; do not rewrite them. Required scenario ids are cold_a, resume_a, cold_b, resume_b, mix_c, mix_d. For each pair, cold_*.recall_at_10 and resume_*.recall_at_10 must match within 1e-4; bank_epoch must equal the durable tip (not the live tip); temperature must sit in the band published under /app/docs/embed_bands.md. Surface probe `/app/data/fixtures/surface_ok.json` may look healthy while bands_ok is false. The report must come from rebuilding/running the engine; hand-written JSON fails. Two consecutive entrypoint runs must be byte-identical.
```

Associated Skills:
```
contrastive embedding eval; temperature schedules; checkpoint resume parity; calibration bank epochs; recall@k bands; NMI agreement; rebuilt inference engines; durable tip binding
```

Task Tags:
```
embeddings, temperature, calibration-bank, checkpoint-resume, recall-at-k, inference-eval
```

- **Why this category is correct:** Goal is inference/eval meeting documented metric bands via a rebuilt engine — ML primary activity, not “fix a script.”
- **Why the Task is Difficult:** Temperature × bank epoch × resume parity couple; greening surface_ok or one cold scenario fails mix/resume cells.
- **Hidden Reasoning Challenges:** Live tip bait vs durable bank_epoch; temperature from wrong schedule sheet; resume packing that silently changes embedding norms.
- **Why This Idea is Original:** Distinct from `int8-calbank-kernel-lane-cutover` (INT8 top1), `lora-adapter-attribution-merge` (adapter merge), and `spec-decode-kv-recalibrate` (speculative decoding).

---

## 6. MoE Router Load-Balance Eval Desk

**Idea Category:** Machine Learning / Model Training / Inference

Task Idea Summary:
```
Seat the mixture-of-experts inference desk so `/app/scripts/run_moe_eval.sh` emits `/output/moe-eval.json` containing schema_tag (string), experts (array of {id:string, load_share:number, active:boolean}), slices (array of {id:string, perplexity:number, expert_entropy:number, router_temp:number}), and eval_ok (boolean). Materials under /app/data/experts/, /app/data/routers/, and /app/data/eval/ are frozen. Load shares across active experts must sum to 1.0 ± 1e-6; each slice perplexity must lie in the band in /app/docs/moe_bands.md; router_temp must match the durable router tip; held experts must have active=false and zero load_share. `/app/tools/moeprobe` may report balanced while eval_ok is false. Verifier rebuilds from /app/eng and re-invokes eval; hardcoded reports fail. Run-twice must be byte-identical.
```

Associated Skills:
```
mixture-of-experts routing; load-share balance; router temperature; held-expert zeroing; perplexity bands; inference eval rebuild; durable router tips; multi-slice agreement
```

Task Tags:
```
mixture-of-experts, router, load-balance, perplexity, inference-eval, held-expert
```

- **Why this category is correct:** Primary work is getting MoE inference/eval metrics into documented bands through the eval engine.
- **Why the Task is Difficult:** Router tip, hold mask, and load renormalization interact; disabling one expert without renormalizing breaks sum and distant slices.
- **Hidden Reasoning Challenges:** Softmax temperature source; held vs dropped expert; surface balanced probe uses uniform shares as bait.
- **Why This Idea is Original:** No MoE router seating task in the repo; not a LoRA/INT8/spec-decode clone.

---

## 7. Offline-Online Feature Skew Calibration

**Idea Category:** Machine Learning / Model Training / Inference

Task Idea Summary:
```
Calibrate the tabular serving stack so `/app/scripts/run_feature_eval.sh` writes `/output/feature-eval.json` with schema_tag (string), features (array of {name:string, offline_mean:number, online_mean:number, skew:number, source:string}), slices (array of {id:string, auc:number, brier:number}), and calibration_ok (boolean). Offline stores under /app/data/offline/ and online snapshots under /app/data/online/ are frozen. For every graded feature, abs(skew) must be ≤ the per-feature bound in /app/docs/skew_bands.md; slice auc/brier must meet those bands; source must be the durable store tip (not the live shadow). `/app/tools/feathealth` may print aligned while calibration_ok is false. Report is produced only by rebuilding/running the engine under /app/eng. Two runs → byte-identical /output/feature-eval.json.
```

Associated Skills:
```
offline-online feature stores; skew bands; AUC and Brier calibration; durable store tips; serving eval rebuild; multi-slice metrics; shadow vs durable sources; idempotent eval reports
```

Task Tags:
```
feature-store, offline-online, skew, auc, brier, serving-eval
```

- **Why this category is correct:** Framing is calibration/eval of a serving model against metric bands — machine learning, not ETL (fixtures stay frozen; solver does not “process files into a report” by hand).
- **Why the Task is Difficult:** Per-feature skew bounds × slice metrics × durable tip couple; fixing means alone can break Brier; shadow store greened by feathealth.
- **Hidden Reasoning Challenges:** Which store is durable; skew definition (online−offline vs ratio bait); slice that only fails when one high-cardinality feature uses live shadow.
- **Why This Idea is Original:** Distinct from LoRA attribution and INT8 cal-bank; feature-store skew seating is not present as a shipped task.

---

## 8. Hex Territory Contest Booklet

**Idea Category:** Interactive / Simulation Tasks / Games

Task Idea Summary:
```
File a Hex tournament card at `/output/hex-card.json` covering twelve Black-to-move positions under `/app/puzzles/`. Schema: schema_tag (string), rounds (array of {board_id:string, status:string, winning_side:string, key_cells:array of string, refutations:array of {cell:string, reply:string}, coop_linkable:boolean}). Status vocabulary and stone-count floors are under `/app/docs/` (`tournament_card.md`, `table_judge.md`). Use sealed judge `/app/bin/judge.jar` and house notes; sensei whisper `/app/tools/sensei_hint.sh` is surface-only and not the card verdict. For unwinnable rounds, every initial threat cell needs a White reply in refutations (coverage, not exact set equality beyond required ⊆). Do not modify the sealed judge or puzzle bytes. Emitting the card via `/app/kiosk/emit_card.sh` twice must be byte-identical.
```

Associated Skills:
```
Hex connection strategy; tournament card filing; sealed table judge; refutation coverage; cooperative vs forced links; contest score sheets; puzzle booklet reasoning
```

Task Tags:
```
hex, territory-contest, tournament, score-card, table-judge, puzzle-book
```

- **Why this category is correct:** Primary activity is deciding contest outcomes under a sealed judge/rulebook — games, not engine repair or forensics.
- **Why the Task is Difficult:** Forced vs cooperative linking misclassifies several boards; refutation coverage and floors resist short liberty-style search padding.
- **Hidden Reasoning Challenges:** Sensei false-green; overnight printer drafts disagree with judge; status vocabulary (win/trap/fort) coupling across distant rounds.
- **Why This Idea is Original:** Existing games are weiqi/blindfold capture contests; Hex connection booklet is a different ruleset and board topology.

---

## 9. Shogi Tsume Drop Contest

**Idea Category:** Interactive / Simulation Tasks / Games

Task Idea Summary:
```
Produce `/output/tsume-card.json` for ten Black-to-move tsume rounds under `/app/puzzles/`. Fields: schema_tag (string), rounds (array of {board_id:string, status:string, mate_in:integer, sequence:array of string, drops_used:array of string, sidelines:array of {move:string, reply:string}, coop_mate:boolean}). House rules for drop legality, check announcements, mate-length floors, and sideline coverage live under `/app/docs/`. Sealed judge: `/app/bin/judge.jar`. Kiosk drafts under `/app/kiosk/` may disagree with the judge; sensei under `/app/tools/` only checks surface fillability. Hand-written cards that fail judge re-entry fail grading. Running `/app/kiosk/emit_card.sh` twice must yield byte-identical output. Leave judge and puzzle fixtures unchanged.
```

Associated Skills:
```
shogi tsume; drop piece legality; mate-length floors; sideline refutations; sealed contest judge; tournament card schema; cooperative vs forced mate
```

Task Tags:
```
shogi, tsume, drop-contest, tournament, table-judge, puzzle-book
```

- **Why this category is correct:** Contest booklet + sealed judge decisions; tournament language throughout.
- **Why the Task is Difficult:** Drop inventory × check order × sidelines; coop_mate traps look winnable under pass-like defense but fail forced mate.
- **Hidden Reasoning Challenges:** Illegal drop bait in kiosk drafts; mate_in padding vs irreducible length; sideline ⊆ required threats.
- **Why This Idea is Original:** No shogi/tsume task in `tasks/` or ready-to-submit zips; distinct from weiqi capture contests.

---

## 10. Reversi Corner-Mobility Contest

**Idea Category:** Interactive / Simulation Tasks / Games

Task Idea Summary:
```
Submit `/output/reversi-card.json` for eleven Black-to-move midgame rounds under `/app/puzzles/`. Schema: schema_tag (string), rounds (array of {board_id:string, status:string, best_move:string, mobility_delta:integer, corner_safe:boolean, refutations:array of {move:string, reply:string}, coop_sweep:boolean}). Rulebook, announce customs, and mobility floors are under `/app/docs/`. Grade with sealed `/app/bin/judge.jar`; `/app/tools/sensei_hint.sh` is non-authoritative. Unwinnable/trap rounds require refutation coverage for every graded losing first move listed in the house notes. Do not alter judge or puzzles. `/app/kiosk/emit_card.sh` run twice must produce byte-identical `/output/reversi-card.json`.
```

Associated Skills:
```
reversi mobility; corner safety; tournament filing; sealed judge validation; refutation coverage; cooperative sweep traps; contest score cards
```

Task Tags:
```
reversi, mobility-contest, tournament, score-card, table-judge, puzzle-book
```

- **Why this category is correct:** Playing/deciding under sealed judge and contest docs — Interactive / Simulation / Games.
- **Why the Task is Difficult:** Corner-safe ≠ max mobility; coop_sweep traps green under naive greedy discs; refutations couple to status across the booklet.
- **Hidden Reasoning Challenges:** Printer drafts with disc-count heuristic; sensei greening traps; exact best_move vs any legal move that meets floors.
- **Why This Idea is Original:** No reversi/othello contest in the repo; avoids weiqi/chess kriegspiel SE classifier traps by staying fully tournament-framed.

---

## Final check matrix

| # | Form category | Alignment | Well-specified | Verifiable | Distinct from |
|---|---------------|-----------|----------------|------------|---------------|
| 1 | System… | ✓ autofs seating | ✓ paths+schema+idempotence | ✓ JSON+re-entry | nfs/backup/iouring |
| 2 | System… | ✓ libvirt attach | ✓ | ✓ | dm-thin/block-volume |
| 3 | System… | ✓ chrony seat | ✓ | ✓ | systemd-cascade |
| 4 | System… | ✓ haproxy seat | ✓ | ✓ | unit-cascade |
| 5 | ML… | ✓ embed eval bands | ✓ | ✓ | int8/lora/spec-decode |
| 6 | ML… | ✓ MoE eval | ✓ | ✓ | (none similar) |
| 7 | ML… | ✓ feature skew eval | ✓ | ✓ | (none similar) |
| 8 | Games… | ✓ Hex contest | ✓ | ✓ | weiqi/blindfold |
| 9 | Games… | ✓ Shogi tsume | ✓ | ✓ | weiqi |
| 10 | Games… | ✓ Reversi contest | ✓ | ✓ | weiqi |

Blocked form categories (Build, Security, Scientific) intentionally unused per open-taxonomy policy.
