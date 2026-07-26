### Decision
GO — Attempt 1. System-administration idmap cutover: live `/etc/samba` + `/var/lib/samba` end-state via ops entrypoints; prebuilt/fixture `wbinfo` surface; three coupled loci (drop-in range fold, roster-vs-decoy authority, reload rematerialize + seal_gen); opaque symbols; false-green `smbclient -L`; no real AD; not source-debug of Samba C.

### Metadata
- version: 2
- Task name: samba-winbind-idmap-cutover
- Title: Samba Idmap Range Cutover
- Category: system-administration
- Languages: [C, bash, Go]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [samba, winbind, idmap, service-cutover, dropin-policy]
- Milestones: 0

## Authoring Brief

### Public contract

Configure a lab Samba/winbind join so AD-style principals resolve into the correct local uid/gid ranges after an idmap backend cutover. Single container, unprivileged fixtures (no real AD domain). Surface `smbclient -L` (or lab `smblist`) may look OK while idmap ranges are wrong.

**Required end state:**
- `/etc/samba/smb.conf` plus drop-ins under `/etc/samba/smb.conf.d/` leave lab `wbinfo -n` / `wbinfo -S` (or `/app/bin/wbinfo` fixture shim) mappings for **every** principal in `/etc/samba/idmap.roster` inside that principal’s declared range.
- `/output/idmap-cutover.json` contains:
  - `status` (string) = `ok`
  - `backend` (string) — active idmap backend id
  - `seal_gen` (integer or string) — must equal contents/value of `/etc/samba/desk.seal`
  - `principals` (array) — one row per roster principal with `name`, `sid`, `uid`, `gid`, `range`
- A decoy range present in conf must **never** appear in the report or in live mappings for roster principals.
- Two runs of `/app/ops/run_idmapseat.sh` and one `/app/ops/run_reload.sh` leave the same report and the same `/var/lib/samba/idmap.tdb` (or lab equivalent) mappings.
- Share-list OK alone is not success.

**Constraints:**
- `[environment] allow_internet = false`
- No multi-container; no privileged AD join
- Primary activity is ops cutover of conf/drop-ins/tdb/report via shipped entrypoints — not rewriting Samba daemon sources
- Fixture AD roster + simulated winbind state under `/var/lib/samba/` and `/app/lab/`

### Failure topology

Cluster A: drop-in lexical/fold order still prefers a legacy backend or wrong base range, so `wbinfo` maps roster SIDs outside declared ranges while smb.conf “looks” present. Cluster B: decoy range stanza remains selected for some principals (or report includes decoy), because roster authority is not applied when materializing mappings. Cluster C: naive conf edits are undone on reload — `run_reload.sh` rematerializes legacy prefer from a sealed journal / preflight, and `seal_gen` stays stale unless activation/meta rewrite runs.

These interact: fixing only ranges without roster filter leaves decoy in the report; fixing report JSON by hand fails reload/tdb re-entry; fixing drop-ins without reload authority fails the second seat/reload pair.

### Environment shape

- **`environment/ops/`** — `run_idmapseat.sh`, `run_reload.sh`, and opaque helpers that fold drop-ins / write tdb / emit report (fix loci live here or in small C/Go tools they call).
- **`environment/bin/`** — prebuilt or image-built `wbinfo`/`smblist` shims that read live lab state (correct when state is correct); false-green `smblist` ignores idmap.
- **`environment/samba-lab/`** or seeded paths materialized to `/etc/samba/`, `/var/lib/samba/` at image start — roster, desk.seal, conf.d, idmap.tdb template.
- **`environment/config/`** — operator notes (layout only; no repair checklist / answer ranges).
- **`environment/docs/`** — report field meanings at outcome level.
- **`environment/data/fixtures/`** — frozen seed principals/SIDs (integrity ledger; do not rewrite).
- **`environment/decoy/`** — helpers that rhyme with fix symbols but only drive smblist smoke.

### Required artifacts

- `tasks/samba-winbind-idmap-cutover/instruction.md` — configure/bring-up framing (not “debug winbind”); name output JSON fields; decoy must not appear; two seats + reload idempotence; smblist insufficient.
- `tasks/samba-winbind-idmap-cutover/task.toml` — `category = "system-administration"`, `allow_internet = false`
- `tasks/samba-winbind-idmap-cutover/output_contract.toml`
- `tasks/samba-winbind-idmap-cutover/environment/Dockerfile` + `.dockerignore`
- `tasks/samba-winbind-idmap-cutover/tests/test.sh` + `test_outputs.py` (≥8 tests)
- `tasks/samba-winbind-idmap-cutover/solution/solve.sh` — ops chain; ≥30 LOC substantive
- Environment tree per Initial Draft Commitments (25+ files)

### Test plan

1. **test_report_schema** — `/output/idmap-cutover.json` has `status=ok`, `backend`, `seal_gen`, `principals[]` with required keys.
2. **test_seal_match** — `seal_gen` equals `/etc/samba/desk.seal`.
3. **test_roster_complete** — every roster name appears exactly once in `principals`.
4. **test_ranges_hold** — each row’s `uid`/`gid` fall inside that row’s `range` (and match live `wbinfo` shim).
5. **test_decoy_absent** — decoy range token/sid never appears in report or tdb mappings for roster users.
6. **test_tdb_agree** — `/var/lib/samba/idmap.tdb` (lab format) agrees with report uids for roster SIDs.
7. **test_seat_twice** — second `run_idmapseat.sh` leaves byte-identical report + tdb digest.
8. **test_reload_stable** — after `run_reload.sh`, report/tdb still match (legacy prefer not restored).
9. **test_smblist_insufficient** — forcing only smblist-green state without idmap fix still fails range/roster tests (or document that tests don’t credit smblist).
10. **test_fixtures_frozen** — `/app/data/fixtures/` (or declared seed) hash unchanged.

Multiple valid ops sequences OK if outcomes hold. Reload/seat-twice depend on prior successful materialize.

### Drafting guardrails

Instruction: **configure / bring up** language, not diagnose/fix. Do not paste the numeric uid ranges as an answer key beyond “declared range in roster.” Do not require real `wbinfo` against a live AD. Opaque fix symbols (`fold_a`, `bind_b`, `emit_c`). Decoy conf stanzas must be real competing authority, not commented “WRONG.” No AI scaffolding filenames. Category tags stay ops (`idmap`, `service-cutover`), not `debug`/`forensics`.

### Triviality Ledger

- Editing only `smb.conf` backend string without drop-in fold still loses to a later conf.d fragment on seat.
- Hand-writing `/output/idmap-cutover.json` fails tdb agree + seat-twice + reload re-entry.
- Mapping everyone into one wide range greens a naive “in range” check if tests are weak — blocked by per-principal roster ranges + decoy absence.
- Running only `smblist` keeps surface green while range tests fail.
- Reload without meta/`seal_gen` rewrite restores legacy prefer (preflight rematerialize).

### Per-gate Pitfall Inventory

- **RC1**: Oracle adds ops logic across three helpers, not comment deletes.
- **RC2**: No broken_/buggy_/golden_ in solver-visible names.
- **RC3**: Assert uid/gid∈range, decoy absent, seal match, tdb agree — not schema-only.
- **RC4/RC5**: Expected SIDs/ranges live in frozen fixtures + tests; not a writable “expected.json” under environment answers.
- **RC6**: Instruction outcomes/symptoms; no “set idmap config = rid” recipe dump.
- **RC7**: solve.sh ≥30 LOC substantive ops.
- **GX9/GX10**: Do not recite every uid in instruction; no polarity contradictions on status.
- **static**: allow_internet=false; 20+ env files; .dockerignore; no COPY of hidden dotdirs.
- **category**: Lead with configure idmap cutover / live mappings — never “find the winbind bug.”

### Initial Draft Commitments

- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/ops/run_idmapseat.sh`
- `environment/ops/run_reload.sh`
- `environment/ops/fold_a.c`
- `environment/ops/bind_b.c`
- `environment/ops/emit_c.go`
- `environment/ops/Makefile`
- `environment/bin/wbinfo`
- `environment/bin/smblist`
- `environment/bin/idmapctl`
- `environment/samba-seed/smb.conf`
- `environment/samba-seed/smb.conf.d/00-base.conf`
- `environment/samba-seed/smb.conf.d/40-legacy.conf`
- `environment/samba-seed/smb.conf.d/90-decoy.conf`
- `environment/samba-seed/idmap.roster`
- `environment/samba-seed/desk.seal`
- `environment/samba-seed/idmap.tdb.template`
- `environment/scripts/materialize_lab.sh`
- `environment/config/paths.toml`
- `environment/config/field-notes.txt`
- `environment/docs/report-schema.md`
- `environment/docs/ops-overview.md`
- `environment/data/fixtures/principals.jsonl`
- `environment/data/fixtures/anchor.sha256`
- `environment/decoy/scan_fold.go`
- `environment/decoy/bind_probe.c`
- `environment/decoy/emit_trace.sh`
- `environment/lib/lab_io.c`
- `environment/lib/lab_io.h`
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `tests/test.sh`
- `tests/test_outputs.py`
- `solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/ops/fold_a.c
  symbol: fold_a
  kind: function
  signature: int fold_a(const char *root, struct MapX *out)
  purpose: Merges conf fragments under root into an ordered map of backend and range lines.

- path: environment/ops/bind_b.c
  symbol: bind_b
  kind: function
  signature: int bind_b(const struct MapX *m, const char *roster, const char *tdb)
  purpose: Writes sid-to-id mappings into the lab tdb from the active map and roster file.

- path: environment/ops/emit_c.go
  symbol: EmitC
  kind: function
  signature: func EmitC(tdb string, seal string, out string) error
  purpose: Reads live mappings and seal file, writes the cutover JSON report.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/ops/fold_a.c
    controls_tests: [test_ranges_hold, test_report_schema, test_smblist_insufficient]
  - id: B
    path: environment/ops/bind_b.c
    controls_tests: [test_roster_complete, test_decoy_absent, test_tdb_agree]
  - id: C
    path: environment/ops/emit_c.go
    controls_tests: [test_seal_match, test_seat_twice, test_reload_stable, test_fixtures_frozen]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/scan_fold.go
  kind: helper
  rhymes_with: fold_a
  non_fix_purpose: Lists conf.d filenames for smblist smoke; does not merge range authority.

- path: environment/decoy/bind_probe.c
  kind: helper
  rhymes_with: bind_b
  non_fix_purpose: Prints tdb key count for diagnostics; does not apply roster filter.

- path: environment/decoy/emit_trace.sh
  kind: helper
  rhymes_with: EmitC
  non_fix_purpose: Dumps raw conf snippets to stderr for operators; does not write /output.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [samba, winbind, idmap, roster, principal, principals, backend, range, decoy, seal, reload, seat, drop-in, dropin, mapping, uid, gid, sid, wbinfo, smblist, cutover, report, status, domain, ad]
```
