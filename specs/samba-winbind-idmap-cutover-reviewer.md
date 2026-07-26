### Decision
GO — Attempt 1. System-administration Samba/winbind idmap cutover; three coupled ops loci; fixture AD; false-green share list; opaque symbols; not Samba source debugging.

### Metadata
- Task name: samba-winbind-idmap-cutover
- Title: Samba Idmap Range Cutover
- Category: system-administration
- Languages: [C, bash, Go]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [samba, winbind, idmap, service-cutover, dropin-policy]
- Milestones: 0

### Discovery budget
- Discovery: conf.d fold order / prefer still selects legacy backend or wrong base; `fold_a` must apply equality-inclusive or documented fold so roster ranges win.
  Planned location: `environment/ops/fold_a.c`
  Why instruction must not reveal it: Naming the winning drop-in filename collapses to a one-file sed.

- Discovery: decoy range stanza must be excluded using roster membership when writing tdb; presence in conf is not authority.
  Planned location: `environment/ops/bind_b.c`
  Why instruction must not reveal it: “Ignore decoy” as a named file is a checklist; discovery is behavioral via report/tdb.

- Discovery: reload rematerializes legacy prefer and stale seal unless emit/meta path rewrites `seal_gen` from `desk.seal` after a successful bind.
  Planned location: `environment/ops/emit_c.go` + `run_reload.sh` preflight
  Why instruction must not reveal it: Publishing the rematerialize hook turns the task into “call this function.”

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest outcomes still need fold×roster×reload.
2 Hidden-instance: PASS — systemic for all roster principals.
3 Single-artifact repair: PASS — three loci.
4 Generalization: PASS — multi-principal roster + decoy + reload.
5 Prompt-honesty: PASS — configure/outcomes; no uid answer table.
6 Cheating-vs-difficulty: PASS — ops coupling.
7 Mechanical-fix filter: PASS — N/A at idea stage.
8 Localized-fix: PASS — fold_a / bind_b / EmitC.
9 Oracle-locality: PASS — ≥3 files.
10 Small declarative-cluster: PASS — drop-ins interact with reload authority.
11 Grep-collapse: PASS — opaque symbols; forbidden instruction nouns on fix path.
12 Pre-factored-helper: PASS — decoy scan/bind_probe/emit_trace.
13 Recipe-discount: PASS — not textbook “install samba and join.”
14 Security-aura: PASS — sysadmin idmap, not admit-lattice cosplay.
15 Orthogonal-checklist: PASS — loci interact.
16 Harness-discount: PASS — fixtures are realism.
17 One-pass solvability: PASS — needs seat/reload experiments.
18 Hard-only gate: PASS.
19 Discovery budget: PASS — three items.
20 Instruction specificity: PASS — outcomes, not recipes.
21 Topology distribution: PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)
1. **Fold-first**: fold_a + bind_b + EmitC — chosen realization.
2. **Tdb-first**: hand-patch tdb + leave fold wrong — fails reload rematerialize and seat-twice.
3. **Report-only**: forge JSON + leave conf/tdb wrong — fails tdb agree and probe/wbinfo checks.

### Rubric axes
1 Verifiable: Pass — JSON + tdb + wbinfo shim + seal file.
2 Well-specified: Pass — fields and idempotence named.
3 Solvable: Pass — Samba/idmap operator in a few hours on fixtures.
4 Difficult: Pass — fold×decoy×reload coupling.
5 Interesting: Pass — real AD idmap cutover pain.
6 Outcome-verified: Pass — mappings/report, not process.

### Hardness axes
- Discover: Winning drop-in fold, roster-vs-decoy, reload rematerialize from code/behavior.
- Synthesize: Conf fold, tdb bind, and report/seal must agree.
- Diagnose: Instruction states configure outcomes, not causes.
- Navigate coupling: One-locus fixes fail decoy, ranges, or reload.
- Reason beyond training: Not “apt install samba”; fixture idmap authority lattice.

### Instruction completeness test
No — does not name which conf.d wins, how decoy is excluded, or what reload rewrites. Agent must run seat/reload and inspect lab state.

## Reviewer Appendix

### Implementation plan
Image materializes `/etc/samba` and `/var/lib/samba` from `samba-seed/`. Broken defaults: fold prefers legacy/decoy; bind writes all conf ranges including decoy; emit omits seal or reads stale gen; reload restores legacy. Shims `wbinfo`/`smblist` read lab files. Oracle fixes `fold_a`, `bind_b`, `EmitC` and runs seat twice + reload. Tests assert roster ranges, decoy absence, seal match, tdb agree, idempotence.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥28 environment files excl. Dockerfile).

### Oracle notes
`solve.sh` patches `fold_a` so ordered merge yields roster backend + per-principal ranges (decoy not selected); patches `bind_b` to apply only roster SIDs into tdb; patches `EmitC` to set `seal_gen` from `desk.seal` and principals from live tdb; runs `run_idmapseat.sh` twice and `run_reload.sh` once; confirms report stable.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate conf fold, roster-filtered tdb bind, and seal-aware emit under reload — not a one-line backend= flip.

Likely editable frontier:
- ops/fold_a.c
- ops/bind_b.c
- ops/emit_c.go
- possibly run_reload.sh preflight

Requirement-to-file map:
- wrong ranges -> fold_a
- decoy in report/tdb -> bind_b
- seal/reload churn -> EmitC / reload

Oracle estimated complexity: 80–140 non-boilerplate lines

Red flags:
- Do not require real winbindd/AD (Harbor unprivileged)
- Do not let smblist alone satisfy tests
- Keep instruction as configure/cutover, not debug

Residual hardness:
Drop-in fold vs decoy vs reload rematerialize still require experiments after the tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
lab, samba, winbind, join, users, uid, gid, ranges, idmap, backend, cutover, drop-ins, mappings, principal, roster, report, status, seal_gen, decoy, reload, seat, share, list, fixtures, domain

**Renames during drafting:**
- `merge_idmap_conf` → `fold_a`
- `apply_roster_tdb` → `bind_b`
- `write_cutover_json` → `EmitC`

**Test names audited:**
- test_report_schema
- test_seal_match
- test_roster_complete
- test_ranges_hold
- test_decoy_absent
- test_tdb_agree
- test_seat_twice
- test_reload_stable
- test_smblist_insufficient
- test_fixtures_frozen

If grep_resistance applies to test names, rename before ship to opaque forms (e.g. test_k3_schema, test_m8_seal, …).

**Concentration math:**
- Total tests: 10
- L1 (fold_a.c): 3/10 = 0.30
- L2 (bind_b.c): 3/10 = 0.30
- L3 (emit_c.go): 4/10 = 0.40
- Cap: 0.5. Max: 0.40. Status: PASS

### Per-test feasibility pre-check
- test_report_schema: LOW
- test_seal_match: LOW/MEDIUM
- test_roster_complete: MEDIUM
- test_ranges_hold: MEDIUM
- test_decoy_absent: MEDIUM
- test_tdb_agree: MEDIUM
- test_seat_twice: MEDIUM — chain on materialize
- test_reload_stable: MEDIUM — chain on materialize
- test_smblist_insufficient: LOW — structural
- test_fixtures_frozen: LOW

### Draft instruction.md (Step 2b; configure framing)

```
Configure the lab Samba/winbind idmap cutover so every principal listed in /etc/samba/idmap.roster resolves into its declared local uid/gid range. Use /etc/samba/smb.conf and drop-ins under /etc/samba/smb.conf.d/, then materialize via /app/ops/run_idmapseat.sh.

Write /output/idmap-cutover.json with status ok, backend, seal_gen equal to /etc/samba/desk.seal, and a principals array of name, sid, uid, gid, range for each roster entry. A decoy range that appears in conf must not appear in the report or in live mappings. Two seat runs and one /app/ops/run_reload.sh must leave the same report and /var/lib/samba/idmap.tdb mappings. Share listing OK alone is not enough. Leave fixture seeds under /app/data/fixtures/ unchanged. Single-container lab fixtures only (no external AD).
```

### Form paste (Idea Proposal)

**Idea Category:** System / Environment Setup & Configuration

Task Idea Summary:
```
Configure a lab Samba/winbind join so AD users resolve into the correct local uid/gid ranges after an idmap backend cutover. /etc/samba/smb.conf plus drop-ins under /etc/samba/smb.conf.d/ must leave wbinfo -n / wbinfo -S mappings for every principal in /etc/samba/idmap.roster inside that principal’s declared range, with /output/idmap-cutover.json listing status=ok, backend, seal_gen matching /etc/samba/desk.seal, and one row per roster principal (name, sid, uid, gid, range). A decoy range in conf must never appear in the report. Two runs of /app/ops/run_idmapseat.sh and one /app/ops/run_reload.sh must leave the same report and /var/lib/samba/idmap.tdb mappings; smbclient -L OK alone is not enough. Single container, unprivileged fixtures (no real AD).
```

Associated Skills:
```
Samba/winbind administration; idmap backends and ranges; AD SID to uid/gid mapping; drop-in smb.conf management; service reload cutover; JSON ops reports; distinguishing share-list OK from idmap correctness
```

Task Tags:
```
samba, winbind, idmap, service-cutover, dropin-policy
```
