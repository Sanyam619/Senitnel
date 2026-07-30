# EC learnings log

Persistent memory for Sentinel Ultra work: mistakes, fixes, platform surprises, and patterns
that worked. **The agent maintains this file — not the user.**

---

## Agent obligations (mandatory, no user prompt needed)

**At the start of every Sentinel session** (zip ingest, review, fix, preflight, eval triage, or
any task under `tasks/active/`):

1. Read this entire file — especially **Standing rules** and the last 5 session entries.
2. Apply standing rules during all steps in `docs/SENTINEL-PROMPTS.md`.

**At the end of every Sentinel session** (even if work stopped early, user interrupted, or
only Step 0–1 ran):

1. Append a new **Session log** entry below (use the template).
2. If a mistake or insight should apply to all future tasks, also add or update **Standing rules**.
3. Do not wait for the user to say "log this" — logging is automatic.

**When a standing rule prevented a mistake or a repeated failure appears in logs**, promote it
to Standing rules and dedupe older session notes that say the same thing.

---

## Standing rules (distilled from past work)

Read these before every task. Add/update as patterns repeat.

| # | Rule | Source |
|---|------|--------|
| 1 | Read `docs/SENTINEL-PROMPTS.md` and run Steps 0→4 automatically when user drops a zip — do not ask which step. | 2026-07-29 setup |
| 2 | Never edit tracked files in `environment/repo/` — only git metadata hygiene. | AGENTS.md |
| 3 | After any `instruction.md` change, run `sync-problem-statement.sh` before preflight. | Repeated preflight fail |
| 4 | Quality Check blocks on **test_coverage** and **test_faithfulness** only — map both directions before upload. | QUALITY-CHECK.md |
| 5 | Grep tests for `skip`, `skipif`, `importorskip`, bare `exists()`, fail-open try/except before calling upload-ready. | Auto-REMOVE patterns |
| 6 | Do not zip until preflight `--docker` PASS. | EC-REVIEW-CHECKLIST |
| 7 | PR scope: expand OK; reduce/replace → Not Fixable — do not relabel or patch around it. | GUIDELINES.md |
| 8 | User only needs to say "I added foo.zip" — full workflow is in SENTINEL-PROMPTS.md, not pasted prompts. | 2026-07-29 setup |
| 9 | Sub-prompts (instruction-only, tests-only, oracle-only) are conditional branches — not part of the default 4-step flow. | 2026-07-29 setup |
| 10 | This repo is Sentinel EC only — do not apply Terminus/TB3 idea-proposal or category-taxonomy workflows here. | 2026-07-29 setup |
| 11 | Snorkel form is **verdict-dependent**. **Fixable** = 8 confirmations + issue detail + re-upload + files changed + 4 time fields. **Invalid** = PR/Environment checkboxes + required why-unfixable + 2 time fields. **Valid-as-is** = **7 confirmations** + difficulty + 2 time fields (no files/issues/re-upload). | 2026-07-29 form SS |
| 12 | Verdict labels: platform uses **Invalid/Not Fixable**; duplicate field must match SEGMENTS field. | 2026-07-29 form SS |

---

## Session log

Newest entries at the top (reverse chronological).

---

### 2026-07-29 — casbin QC revision (test_coverage gap)

**Steps run:** 5 (eval triage) + fix + re-zip

**Task:** `tasks/active/8959a77b-76de-4981-8878-0344543e8442_submission/`

**Outcome:** Fixable (revised) — added f2p test + instruction updates

**What happened:**
- Platform QC Status OK overall but GPT scored test_coverage 3/5: no dedicated test for instruction's "no role manager → g(name1,name2) equality" clause.
- GPT test_faithfulness 4/5: tests assert DefaultRoleManager.syncedHasLink but instruction didn't document it explicitly.
- Validation logs: oracle_1 reward 1.0, nop 0.0; oracle_2 flake (empty stdout, 0/15 parsed) — infra not task bug.

**Fix applied:**
- Added `TestSyncedEnforcerGEqualityWithoutRoleManager` to tests.patch + config.json (16 f2p).
- instruction.md: document DefaultRoleManager/RoleManager exports, syncedHasLink, clarify "no role manager on g definition".

**Rule for next time:**
- When QC cites a specific instruction clause with no enforcing test, add an f2p test — don't only note it in Comments for Reviewer.
- Document API surface tests assert (syncedHasLink, exports) in instruction for faithfulness.
- Oracle 2/3 flake: if stderr shows `npx` hitting registry.npmjs.org during verify (no-network), switch to `./node_modules/.bin/jest` and fix Dockerfile `yarn install || true` silent failures.

---

### 2026-07-29 — casbin-node-casbin PR378 (8959a77b submission zip)

**Steps run:** 0 / 1 / 2 / 3 / 4

**Task:** `tasks/active/8959a77b-76de-4981-8878-0344543e8442_submission/`

**Outcome:** Fixable (fixed) — preflight PASS, zip created

**What went well:**
- 15 f2p tests, good coverage of RBAC sync/async/domain/transitive/throw paths
- Git hygiene clean, golden.patch matches PR #378, tests.patch applies
- First real end-to-end workflow test from inbox zip

**Mistakes / surprises:**
- Ingest needs full permissions (sandbox disk write fails on .git)
- Preflight FAIL: `[environment] network_mode` was `no-network`, must be `public`
- Test asserts exact throw message but instruction only said "throw an error" — faithfulness gap
- `pass_to_pass` empty (warning only); no dedicated test for "no role manager → g equality"
- zip-task.sh: validate_task.py permission denied (script still zips)

**Fix applied:**
- `task.toml`: environment `network_mode = "public"`
- `instruction.md`: behavioral rewrite + documented exact error message; synced problem_statement

**Rule for next time:**
- Always run preflight after ingest — network_mode in `[environment]` is a common silent FAIL
- When tests assert exact error strings, document them in instruction (faithfulness)
- Ingest with `all` permissions if sandbox blocks .git extraction

---

### 2026-07-29 — EC learnings log created

**Steps run:** other (docs + rules)

**Task:** n/a

**Outcome:** setup complete

**What went well:**
- Single file `docs/EC-LEARNINGS.md` for standing rules + per-session logs.
- Wired into SENTINEL-PROMPTS.md, sentinel-ec.mdc, AGENTS.md, README — agent reads at start, writes at end without user asking.

**Mistakes / surprises:**
- n/a (initial setup)

**Fix applied:**
- Standing rules table + session template + mandatory obligations section at top of file.

**Rule for next time:**
- Log every session, even partial or Not Fixable stops. Promote repeat failures to Standing rules.

---

### 2026-07-29 — repo workflow setup (no task)

**Steps run:** other (docs + rules)

**Task:** n/a — playbook and learnings file created

**Outcome:** setup complete

**What went well:**
- Consolidated Sentinel workflow into single agent playbook (`docs/SENTINEL-PROMPTS.md`) so user only says "I added foo.zip".
- Kept 4 core steps (ingest → review → fix → gate → zip) and moved optional paths to "If this happens…" branches.

**Mistakes / surprises:**
- Initial prompt set had 7–8 separate copy-paste prompts (mirroring Terminus) — too many for Sentinel's review/fix workflow; user confirmed 4 core steps are enough.

**Fix applied:**
- Rewrote SENTINEL-PROMPTS.md as agent-executed playbook, not user copy-paste blocks.
- Updated `.cursor/rules/sentinel-ec.mdc` to auto-run workflow from playbook.

**Rule for next time:**
- Sentinel ≠ Terminus: no idea proposals, category taxonomy, or canonical-image prompts here.
- Default to Steps 0→4 automatically; use conditional branches only when situation matches.

---

### Entry template (copy for new sessions)

```
### YYYY-MM-DD — `<task-name or topic>`

**Steps run:** 0 / 1 / 2 / 3 / 4 / eval-triage / other

**Task:** `tasks/active/<name>/` (or "no task")

**Outcome:** Valid as-is | Fixable (fixed) | Fixable (partial) | Not Fixable | blocked

**What went well:**
-

**Mistakes / surprises:**
-

**Fix applied:**
-

**Rule for next time:**
-
```
