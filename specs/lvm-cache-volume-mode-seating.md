### Decision
GO — Hard system-administration LVM cache-volume mode seating desk. Coupled preference-gated rematerialize × sealed mode-journal tip resolution × durable generation floors × maintenance-window polarity × lexical drop-in fold with abort synonyms × sealed cachepool identity × canonical idempotent ledger emit. Primary activity is bringing live `/etc/lvm` + `/var/lib/lvm` ops state to a correct durable end-state, not software repair or debugging.

### Metadata
- version: 2
- Task name: lvm-cache-volume-mode-seating
- Title: LVM Cache Volume Mode Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["lvm-cache", "cache-mode", "cachepool", "hold-window", "mode-journal", "generation-gate"]
- Milestones: 0

## Authoring Brief

### Public contract
Live cache materials under `/etc/lvm/` must agree with the durable volume authority under `/var/lib/lvm/`. Entrypoint `/app/ops/run_lvmcache_seat.sh` must produce `/output/lvmcache-seat.json` with:

- `schema_tag` (string) equal to `lvmcache-seat-v1`
- `volumes` — array of `{name:string, vg:string, mode:string, cachepool:string, generation:int, attached:bool}`
- `holds` — array of `{lv:string, until_epoch:int}`
- `seat_ok` (boolean)

Surface `/usr/local/bin/lvmhealth` may print OK while deep seating is wrong. Frozen fixtures under `/app/data/lvm/` stay integrity-pinned and their sealed copies under `/var/lib/lvm/ops/` must keep matching them. A volume is `attached` only when its sealed tip generation is at or above the durable floor (equality inclusive), no open maintenance window covers it, the live sheet carries the sealed cachepool identity and the durable tip mode, and the folded drop-in policy does not name it as the abort target. Two seating passes must leave `/output/lvmcache-seat.json` byte-identical.

### Failure topology
Authorities couple. A preflight refreshes every live cache sheet from the pre-cutover working sheet on each pass — and drops the apply receipt — unless the material plane selects durable AND `/var/lib/lvm/ops/state/apply.ok` carries `gen=<target>` with `mode=seal`; on the durable plane with a matching receipt it must instead refresh the live sheets from the sealed durable image (journal tip modes plus sealed cachepool UUIDs) and leave the live drop-ins alone. Tip resolution is the cutover row whose generation equals `gen.target` and whose mode is sealed — an older sealed window and a later provisional re-open are history, and one volume's sealed tip sits below the durable floor while the decoy live floors would wrongly admit it. Maintenance windows compare strictly against the desk clock, so an expired window must not exclude its volume while an open one must. Drop-ins fold in lexical order with last-wins, and the forensic abort package carries `abort=<name>` synonyms that the site standard clears — a first-wins fold or a rematerialized abort package silently unseats a volume that should attach. The working sheet marks every volume writeback, so any ledger that reports live modes fails the mode column even when attachment polarity is right. Greening `lvmhealth` or hand-editing `/etc/lvm` still fails distant cells because the verifier clears `/output` and re-enters the desk twice.

### Environment shape
- Broken ops helpers under `/app/ops`, `/app/rim`, `/app/bag`, `/app/deck`
- Decoy helpers beside them doing genuine non-graded work (`/app/wire`, `/app/rim`, `/app/bag`)
- Live host state under `/etc/lvm` (drop-in policy, cache mode sheets, decoy floors, roster) and `/var/lib/lvm` (durable floors, maintenance windows, state plane, sealed map, mode journal, material preference, working sheet, forensic abort package)
- Immutable fixtures under `/app/data/lvm` plus a packaging digest under `/app/packaging`
- Outcome docs under `/app/docs`; site standard under `/app/config`
- Surface health bait `/usr/local/bin/lvmhealth`
- Correct publisher `/app/bin/cacheseat` reads prepared state; the shipped emitter does not call it

### Roster / attach matrix (design target, sealed journal gen.target=9)
| name | vg | durable mode | tip gen | floor | window | attached |
|------|-----|--------------|---------|-------|--------|----------|
| alpha | vg0 | writethrough | 12 | 10 | none | yes |
| beta | vg0 | writeback | 8 | 10 | none | no — tip below floor |
| gamma | vg1 | passthrough | 15 | 10 | open | no — window open |
| delta | vg1 | writethrough | 14 | 10 | expired | yes |
| epsilon | vg2 | writeback | 11 | 10 | none | yes |
| zeta | vg2 | writethrough | 20 | 10 | none | yes (abort cleared by site standard) |

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (44 files excl. Dockerfile), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`, `environment/.dockerignore`, hashed `requirements.txt`.

### Test plan
- `test_q3_topaz` — ledger schema, schema tag, field types, settled desk
- `test_n4_beryl` — two seating passes byte-identical
- `test_w7_quartz` — frozen fixture digest pin + sealed copy equals the pinned mirror
- `test_j2_onyx` — folded effective policy carries the site-standard tokens
- `test_v5_coral` — tip generation versus durable floor; below-floor volume unseated
- `test_p9_jade` — open window blocks; expired window does not
- `test_h8_amber` — abort package stays forensic, live drop-in stays site-standard, abort-named volume attaches
- `test_c1_flint` — durable material plane plus matching receipt; live generation equals target
- `test_r6_slate` — cachepool identity and modes are the sealed/durable ones in both ledger and live sheets
- `test_u2_mica` — maintenance window array recomputed from durable window files
- `test_m1_opal` — full roster attach matrix, generations, vgs, modes, cachepools
- `test_t4_pearl` — surface probe prints OK while deep seating still has to agree
- `test_k5_garnet` — re-entry restores a tampered report and attached rows never carry working-sheet modes

Each test accepts any correct seating end-state; none require oracle-only paths. Not chain-dependent: the module fixture re-enters the full entrypoint twice and several tests re-enter again.

### Drafting guardrails
Symptoms-only instruction with a closing vocabulary list; acceptance rules (floor inclusivity, sealed-row selection, strict window comparison, lexical last-wins fold, receipt format, sealed cachepool identity, drop-in persistence) live in `/app/docs` as desk contract prose, never as a repair checklist. Opaque fix-path symbols from the construction manifest. No intent comments on fix sites. No golden JSON under `environment/`. Verifier clears `/output`, re-enters seating, and derives expectations from the durable fixtures in test code. No repair/debug framing anywhere solver-visible.

### Triviality Ledger
- Hand-writing `/output/lvmcache-seat.json` fails because the verifier deletes the output and re-enters `/app/ops/run_lvmcache_seat.sh` twice.
- Hand-aligning `/etc/lvm/cache.d` fails because the shipped preflight refreshes those sheets from the working sheet and deletes the receipt on every pass until the plane/receipt gate is implemented.
- Flipping `prefer.toml` alone fails because tip resolution, floors, windows, the fold, and the emit still disagree with the durable authority.
- Writing the receipt alone fails because the durable-plane path must also refresh live sheets from the sealed durable image.
- Hardcoding `attached` true fails the below-floor volume and the open-window volume; hardcoding it false fails four rows and the settled-desk assertion.
- Reporting the live working-sheet modes fails the mode column for every volume whose durable tip is not writeback.
- Reading the decoy live floors fails the below-floor volume; using a strict floor comparison fails the equality-inclusive rows.
- Treating any window row as active fails the expired window; ignoring windows fails the open one.
- First-wins fold or a rematerialized abort package unseats the abort-named volume and breaks the effective-policy check.
- Rewriting the frozen fixtures or the sealed map to match wrong live edits fails the digest pin and the sealed-copy equality test.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites five substantive helper bodies with new multi-authority logic (no marker deletion, no comment-only diff).
- RC2: no broken_/golden_/expected_ tokens on solver-visible surfaces; opaque helper names unrelated to instruction nouns.
- RC3: tests assert computed mode/cachepool/generation/attached/window values recomputed from durable fixtures, never schema-only.
- RC4/RC5: expectations derived in test code from the digest-pinned `/app/data/lvm` tree; the live sealed copy is asserted equal to the pin so tampering fails; the digest pin is checked with the packaging digest file, not by re-deriving from agent-writable state.
- RC6: instruction symptoms-only; acceptance rules are outcomes in docs, not fix recipes.
- RC7/GX3: oracle ≈ 206 substantive LOC / 242 real edit lines across five helper bodies.
- CR2: five locations across four roots, max single-location share 45% under the 0.5 cap.
- GX9: no test contract triples recited in the instruction — expected values are computed in test code or compared as whole mappings, so the instruction cannot act as an answer key.
- GX10: attachment polarity is stated per scenario in docs, never both polarities for one case in the instruction.
- Static: `allow_internet=false`; hashed `requirements.txt` with `--require-hashes`; explicit `check=` on every `subprocess.run`; no `v == v` NaN idiom; `.dockerignore` shipped; LF endings; executable bits on every shell script.
- Category: grade live `/etc`/`/var` end-state via bash ops helpers; languages `["bash"]`; storage-ops tags; no repair/debug aura.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/ops/run_lvmcache_seat.sh
- environment/ops/kelp_n.sh
- environment/ops/axle_r.sh
- environment/rim/mesh_p.sh
- environment/rim/scan_b.sh
- environment/bag/skim_w.sh
- environment/bag/note_c.sh
- environment/deck/emit_j.sh
- environment/wire/knit_s.sh
- environment/cli/cacheseat
- environment/cli/lvmhealth
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/config/site_standard.conf
- environment/packaging/README.md
- environment/data/roster.list
- environment/data/lvm/pool.map
- environment/data/lvm/volumes/{alpha,beta,gamma,delta,epsilon,zeta}.toml
- environment/data/seed/prefer.toml
- environment/data/seed/surface.modes
- environment/data/seed/floors.toml
- environment/data/seed/live_floors.toml
- environment/data/seed/holds.toml
- environment/data/seed/journal.jsonl
- environment/data/seed/clock.epoch
- environment/data/seed/abort.d/90-local.conf
- environment/data/seed/lvm.conf.d/{10-core,40-lab,90-local}.conf
- environment/data/seed/cache.d/{alpha,beta,gamma,delta,epsilon,zeta}.conf
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: ops/kelp_n.sh
  symbol: kelp_n
  kind: function
  signature: kelp_n
  purpose: Gate the live-sheet refresh on the selected material plane and a matching apply receipt
- path: ops/axle_r.sh
  symbol: axle_r
  kind: function
  signature: axle_r
  purpose: Apply the sealed window tip generations and cache modes against the durable floors
- path: rim/mesh_p.sh
  symbol: mesh_p
  kind: function
  signature: mesh_p
  purpose: Fold drop-in conf keys in lexical order into the effective policy file
- path: bag/skim_w.sh
  symbol: skim_w
  kind: function
  signature: skim_w
  purpose: Materialize maintenance window state against the desk clock
- path: deck/emit_j.sh
  symbol: emit_j
  kind: function
  signature: emit_j
  purpose: Publish the seating ledger from prepared state and full authority agreement
```

#### flipping_point_contract

```
locations:
  - id: A
    path: rim/mesh_p.sh
    controls_tests: [test_j2_onyx, test_h8_amber, test_m1_opal]
  - id: B
    path: ops/axle_r.sh
    controls_tests: [test_v5_coral, test_r6_slate, test_c1_flint, test_m1_opal]
  - id: C
    path: bag/skim_w.sh
    controls_tests: [test_p9_jade, test_u2_mica, test_m1_opal]
  - id: D
    path: ops/kelp_n.sh
    controls_tests: [test_h8_amber, test_c1_flint, test_r6_slate, test_k5_garnet]
  - id: E
    path: deck/emit_j.sh
    controls_tests: [test_q3_topaz, test_r6_slate, test_u2_mica, test_t4_pearl, test_k5_garnet]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

Coverage note: `test_n4_beryl` and `test_w7_quartz` are cross-cutting (idempotence and fixture integrity) and are exercised by every location; the thirteen graded tests are covered by A–E plus those two invariants.

#### decoy_manifest

```
- path: wire/knit_s.sh
  kind: helper
  rhymes_with: mesh_p
  non_fix_purpose: Writes a shift crumb under /var/log/lvm; not on the seating path
- path: rim/scan_b.sh
  kind: helper
  rhymes_with: axle_r
  non_fix_purpose: Lists roster names for the surface probe
- path: bag/note_c.sh
  kind: helper
  rhymes_with: skim_w
  non_fix_purpose: Archives a non-graded window memo for shift handover
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [lvm, cache, volume, volumes, seating, seat, seat_ok, schema_tag, name, vg, mode, cachepool, generation, attached, holds, lv, until_epoch, durable, authority, journal, identity, window, windows, maintenance, receipt, plane, fold, policy, floor, abort, surface, lvmhealth, fixtures, integrity, roster, ledger, desk, docs, sealed, cutover]
```
