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
| 5b | **f2p count must be 11–20.** Floor 11 because the platform checkbox reads "More than 10". Ceiling 20 is **ours, not the hub's** — observed CodeBuild rejection at 21. | 2026-08-02 opensandbox CI |
| 6 | Do not zip until preflight `--docker` PASS. | EC-REVIEW-CHECKLIST |
| 7 | PR scope: expand OK; reduce/replace → Not Fixable — do not relabel or patch around it. | GUIDELINES.md |
| 8 | User only needs to say "I added foo.zip" — full workflow is in SENTINEL-PROMPTS.md, not pasted prompts. | 2026-07-29 setup |
| 9 | Sub-prompts (instruction-only, tests-only, oracle-only) are conditional branches — not part of the default 4-step flow. | 2026-07-29 setup |
| 10 | This repo is Sentinel EC only — do not apply Terminus/TB3 idea-proposal or category-taxonomy workflows here. | 2026-07-29 setup |
| 11 | Snorkel form is **verdict-dependent**. **Fixable** = 8 confirmations + issue detail + re-upload + files changed + 4 time fields. **Invalid** = PR/Environment checkboxes + required why-unfixable + 2 time fields. **Valid-as-is** = **7 confirmations** + difficulty + 2 time fields (no files/issues/re-upload). | 2026-07-29 form SS |
| 12 | Verdict labels: platform uses **Invalid/Not Fixable**; duplicate field must match SEGMENTS field. | 2026-07-29 form SS |
| 13 | **Skip** when Difficulty FAIL EASY + ~100% agent pass after QC/oracle OK — cannot reach MEDIUM+ without breaking QC/PR rules. Use `docs/SKIP-GUIDE.md` radio + reason. | 2026-08-01 casbin |
| 14 | tests.patch must not create files at paths agents implement (e.g. `src/main/foo.test.ts` beside `foo.ts`). Use verifier-only dirs (`src/verifier/`). Never say "existing tests" for patch-injected files. | 2026-08-02 agent-orchestrator |
| 15 | **Never zip with `node_modules` in `environment/repo/`** — Dockerfile runs `npm ci` at build. Bundling node_modules → 200MB+ zips → Snorkel S3/GuardDuty timeout. Delete before zip; `zip-task.sh` now hard-fails. | 2026-08-02 agent-orchestrator |
| 16 | **Strip `.git/logs` before every zip** — CDG static check fails on reflog. `zip-task.sh` auto-strips + runs `git-hygiene.sh` gate. | 2026-08-02 agent-orchestrator |
| 17 | **Never remove** "do not write/modify tests" from instruction when tests.patch creates new test files — agents writing `*_test.go` causes harness failures (0/8 invalid trials). | 2026-08-02 opensandbox eval |
| 18 | When tests assert exact API names, document every name in instruction — faithfulness blocks on hidden contracts. | 2026-08-02 opensandbox QC |
| 19 | Put eval tests in **`eval_*_test.go`** new files; never patch base `*_test.go` agents may edit. | 2026-08-02 opensandbox harness |
| 20 | After editing golden.patch or tests.patch hunks, **recount `+` lines** in each `@@` header — wrong count truncates files. | 2026-08-02 opensandbox oracle |
| 21 | Strip stray upstream artifacts in **Dockerfile** when packaging judge flags them — cannot edit tracked repo files. | 2026-08-02 opensandbox packaging |
| 22 | **Infra/platform eval failures are not task defects** — retry; use `stb submissions list`; don't mark Unfixable. See `docs/PLATFORM-TRIAGE.md`. | 2026-08-02 hub alignment |
| 23 | **Valid-as-is requires local oracle + NOP** — platform skips difficulty re-run. `preflight.sh` now runs both by default; never gate with `--fast`. | 2026-08-02 hub alignment |
| 24 | When hub guidelines change, diff `docs/hub-scrape/` against condensed docs and update locally. | 2026-08-02 hub alignment |
| 25 | **Revision budget is 2, and eval runs are free.** Iterate on the platform with Send to reviewer *unchecked* until every check is green. See `REVISION-BUDGET.md`. | 2026-08-03 repo audit |
| 26 | The real tests live in **`tests.patch`**, not `tests/*.py` — any test scan that skips the patch inspects nothing. `validate_task.py` reads added patch lines across Python/Go/JS/gtest. | 2026-08-03 repo audit |
| 27 | The hub's HTML scrape drops every `<details>` panel (environment, git, oracle, verifiability tables). Use `docs/hub-scrape/guide-panels.txt`; refresh with `scripts/fetch-hub-panels.py`. No auth needed — the gate is client-side. | 2026-08-03 repo audit |
| 28 | **Every f2p id must be traceable into `tests.patch`**, and `allow_extra_failures` must be `false` — an unmatched id pins the reward at 0 forever. | 2026-08-03 repo audit |
| 29 | Set `[agent] timeout_sec = 7200` (the ceiling). A tight limit fails tasks that would otherwise pass, and Agent Timeout is its own reviewer error category. | 2026-08-03 repo audit |
| 30 | Distinguish hub policy from our experience when writing docs. Only two rules here are ours: the f2p ceiling of 20 and the 2-revision budget. Never cite them to a reviewer as guidelines. | 2026-08-03 repo audit |
| 31 | **`git apply` accepts a patch whose `@@` header undercounts its hunk** — `--check` passes, `--numstat` reports the declared count, and the file applies truncated. Never treat "git accepted it" as patch integrity; compare git's count against the raw `+` lines (`validate_task.py` does). | 2026-08-03 toolchain test |
| 32 | **`git apply --numstat` run inside a work tree silently drops paths outside the current directory** and exits 0 with empty output. Run patch inspection from a scratch dir with `GIT_CEILING_DIRECTORIES` set. | 2026-08-03 toolchain test |
| 33 | **Never trust a green check you have not tested.** `scripts/selftest.py` injects one of each defect class into a throwaway task and asserts the validator catches it; `preflight.sh` and `zip-task.sh` run it before their own verdict. If a check stops firing it looks exactly like a pass. | 2026-08-03 toolchain test |
| 34 | A rule may be summarised in many docs but is **decided in one** (map in `AGENTS.md`). `scripts/check-docs.py` fails on a copy that disagrees with `validate_task.py` or on a dead file reference. When a doc and a check disagree, the check wins. | 2026-08-03 toolchain test |
| 35 | **A gate that reports FAIL must be proven to fail for the right reason.** `preflight.sh` tagged its image `sentinel-preflight-<id cut to 24 chars>`, which ends on a hyphen and is an invalid Docker tag — so it reported "the platform build will fail the same way" against four tasks whose environments all build fine. Sanitise every generated identifier and print it in the message. | 2026-08-03 first full gate |
| 36 | Docker Desktop here allots **4.1 GB** while tasks declare `memory_mb = 8192`. Oracle/NOP still passed, so a local OOM is a laptop limit, not a task defect — check `docker info` before blaming the task. | 2026-08-03 first full gate |
| 37 | **`harbor check` needs your own `ANTHROPIC_API_KEY`** — the Portkey host in `[agent] allowed_hosts` is for the trial agent, not the judge. Without it the judge exits after ~20s; preflight now checks first and prints the export line. | 2026-08-03 rubric wiring |
| 38 | **`git-hygiene.sh`'s "no commits beyond HEAD" cannot see a commit made on HEAD's own branch** — that moves HEAD, so only the `base_commit_sha` comparison catches it. Stray branches and tags are what `rev-list --all --not HEAD` covers. A missing `base_commit_sha` leaves the accidental-commit case unverifiable. | 2026-08-03 shell suite |

---

## Session log

Newest entries at the top (reverse chronological).

---

### 2026-08-03 — Making the gate verifiable (self-test, git-backed patch parsing, doc drift check)

**Steps run:** other (tooling; no task work)

**Task:** n/a — follow-up to the audit below, which left the tooling "probably right" but
untested.

**Outcome:** the checks are now proven rather than asserted. 29 defect classes are injected
into a throwaway task on every preflight and every zip; patch structure comes from `git apply`
instead of a hand-written diff reader; doc/tooling disagreement fails a check instead of
waiting to mislead someone.

**What went well:**
- The self-test caught nothing new in the four active tasks, which is the point — validator
  output before and after is identical, so the rewrite did not change any verdict.
- Sabotage test: lowering `MIN_F2P` and downgrading the auto-REMOVE failure to a warning made
  3 of 29 cases report "defect not caught". The suite fails when the checker is broken.

**Mistakes / surprises:**
- The plan was to *replace* the hand-written hunk-count check with `git apply --numstat`.
  Testing showed git is the wrong authority for that one thing: with a hunk header understated
  by 3 lines, `--check` passed and `--numstat` happily reported the declared count. git applies
  such a patch and truncates the file, silently — exactly the failure seen twice before. Kept
  the count cross-check and used git for what it is authoritative on: create/delete/rename/mode,
  binary detection, path quoting, and whether the patch applies at base at all.
- `git apply --numstat` run with `cwd` inside this repo returned **empty output and exit 0**,
  because a patch path outside the current directory is ignored inside a work tree. That made
  every task report "no parseable diff headers" for one run. Fixed with a scratch cwd plus
  `GIT_CEILING_DIRECTORIES`.
- New capability found while wiring this up: `git apply --check` inside `environment/repo`
  proves both `tests.patch` and `golden.patch` apply at base. A patch that does not apply errors
  every trial, and nothing local checked `golden.patch` before.
- The f2p range was stated in 9 live places. Deleting the copies would have made `AGENTS.md`
  and the Cursor rule — the only files always in context — incomplete. Enforced agreement
  instead of removing duplication.

**Fix applied:**
- `scripts/selftest.py` (new): builds a valid fixture task with a real git repo and
  git-generated patches, then copies it 29 times, injects one defect per copy, and asserts the
  expected failure. Clean case must report zero failures, which is the guard against false
  positives. ~3s.
- `validate_task.py`: `git apply --numstat -z` + `--summary` now supply file classification;
  local scanning is limited to added-line content plus a `+`-line count cross-checked against
  git. Added rename/mode-change/binary handling and `check_patch_applies`.
- `scripts/check-docs.py` (new): policy numbers in prose must match `validate_task.py`
  constants, every `docs/` `scripts/` `templates/` path a doc names must exist, and `.sh`
  references must be executable. `<!-- policy-check: ignore -->` exempts deliberate quotes of
  the hub's older wording.
- `preflight.sh` runs both new scripts as its first section; `zip-task.sh` runs the self-test
  before its own gate.
- `AGENTS.md` gained a "Where a rule lives" map naming the canonical owner of each rule;
  `HARBOR-FORMAT.md` and `REVISION-BUDGET.md` state their ownership at the top.

**First full gate run (same day, once Docker was started):**
- `8959a77b`: **oracle reward 1.0 and NOP reward 0.0** — the first time the expensive half of
  the gate has completed on this machine. ~110s for both trials. `harbor` and `stb` were
  installed all along; every earlier run had been `--fast` or fell into the "harbor not found"
  branch, so this path had been written and never exercised.
- The same run reported `FAIL docker build — the platform build will fail the same way`, which
  was **my own bug, not the task's**: the image tag `sentinel-preflight-${NAME:0:24}` truncates
  a task id to a trailing hyphen, and Docker rejects that as an invalid reference. Fixed by
  sanitising the tag (lowercase, collapse non-alphanumerics, strip leading/trailing hyphens),
  logging the build to `.preflight/<name>/docker-build.log`, printing the tag in the PASS line,
  and failing early with a clear message when the daemon is down. All four environments then
  built clean, including the Go and C++ ones.
- Lesson worth more than the fix: I had been reading a red FAIL as evidence about the task for
  the whole session. A gate needs its failure path tested, not just its success path.

**Closing the three remaining gaps (same session):**
- **Shell layer under test.** `selftest.py` grew a `shell` suite: `git-hygiene.sh` (dirty tree,
  stray tag, remote, sha mismatch, reflog, non-applying patch), `preflight.sh` (clean pass,
  rejects a bad task, docker tag validity for a truncated and a punctuated task name),
  `zip-task.sh` (packs clean, flat layout with `.git` refs kept, refuses `runs/`, strays, an
  invalid task, a dirty repo), `sync-problem-statement.sh`, and a full `ingest-task.sh` round
  trip through `tasks/inbox`. `SENTINEL_SELFTEST=1` breaks the preflight↔selftest recursion.
- **Every pattern exercised.** One case per auto-REMOVE and unfaithful-assertion pattern in the
  language it belongs to — Go `t.Skip`/`testing.Short`, JS `it.skip`/`xit`/`it.only`/empty
  `catch`, gtest `GTEST_SKIP`/`DISABLED_` — plus a `pattern_coverage` assertion that fails if a
  pattern is ever added without a case. 20 of 20 covered.
- **Docs suite.** `check-docs.py` is now tested against a faithful mirror of the doc tree with a
  stale f2p range and a dead script reference injected.
- **Rubric judge:** blocked on credentials, not code. `harbor check` wants `ANTHROPIC_API_KEY`;
  preflight now checks for it up front and prints the export line, and a case asserts that
  message. The judge itself remains unrun — see standing rule 37.
- Total: **73 cases in ~7 seconds.**
- Writing the shell suite surfaced a genuine gap in `git-hygiene.sh` (standing rule 38): my
  first "extra commit" case failed because that check only sees commits on *other* refs. The
  test was wrong about the guarantee; the script now documents what it does and does not cover,
  and both cases exist.

**Next time:**
- Extend `selftest.py` when adding a check — `pattern_coverage` now enforces this for patterns,
  but not for structural checks.
- Oracle/NOP is still unproven on the other three tasks (~2 min each) — run before any upload.
- First successful `harbor check` run: record the JSON shape here, it is currently unknown.

---

### 2026-08-03 — Repo audit against hub docs + toolchain hardening

**Steps run:** other (full repo audit, no task work)

**Task:** n/a — audited `docs/`, `scripts/`, `templates/` against `docs/hub-scrape/`

**Outcome:** docs were already faithful to the hub; the enforcement layer was not. Rewrote
the gate so the local checks match what the platform actually blocks on.

**What went well:**
- No local doc contradicted current hub policy — the condensed guides held up.
- The tables in `GUIDELINES.md` that looked unsourced turned out to be correct.

**Mistakes / surprises:**
- `validate_task.py` skipped `tests.patch` and only scanned `tests/*.py|sh`. Every task here
  is Go/TS/C++, so the auto-REMOVE scan covered **zero** real test code — while emitting a
  false positive on all four tasks from the `grade.py` copy embedded in `test.sh`.
- `zip-task.sh` claimed a "validate gate" in its own comment but never called
  `validate_task.py`.
- `task.toml` validation was whitespace-sensitive string matching with no block awareness
  (a `network_mode = "public"` in `[verifier]` passed) and checked no published limit but `gpus`.
- The oracle/NOP run was opt-in behind `--harbor`, and `harbor`/`stb` were installed all along.
  `harbor check` (a local rubric judge) was never wired up.
- The hub HTML scrape silently dropped every `<details>` panel — the environment, git, oracle,
  and verifiability tables. The hub bundle is public; the email gate is client-side only.
- All four active tasks sit at `[agent] timeout_sec = 1800` against a 7200 ceiling, and 3 of 4
  have empty `pass_to_pass` with `allow_extra_failures: true`.
- Two of miniob's 13 f2p ids resolve to pre-existing tests in `environment/repo`, not to
  `tests.patch`.

**Fix applied:**
- `validate_task.py` rewritten: parses `tests.patch` (added lines) for auto-REMOVE patterns
  across Python/Go/JS-TS/gtest, verifies `@@` hunk counts, flags patches that modify
  pre-existing test files or create files beside implementation code, traces every f2p id
  into the patch, parses `task.toml` with `tomllib` and enforces every published limit,
  checks leakage, `runs/`, executable bits, and packaging.
- `preflight.sh`: docker build + oracle 1.0 + NOP 0.0 now run **by default**; added
  `--rubric` (`harbor check`), `--fast`, `--no-docker`, `--no-oracle`; scratch output moved
  out of the task dir so it can never ship.
- `zip-task.sh`: real gate — validate + git hygiene + stray sweep + `runs/` + post-zip
  verification that the archive is flat, keeps `refs/`, and is under 80 MiB. Fixed a
  relative-output bug that would have written the zip inside the task, and a `pipefail`
  SIGPIPE bug that failed a valid archive.
- Added `scripts/fetch-hub-panels.py` + `docs/hub-scrape/guide-panels.txt` (13 panels).
- Added `docs/REVISION-BUDGET.md`; f2p floor raised to 11 across all docs; provenance labels
  on the two non-hub rules; `HARBOR-FORMAT.md` now documents the real shipped `task.toml`.

**Rule for next time:**
- Verify a claim against the source before calling it unsourced — the "invented" autocorrect
  names were real, just hidden in a collapsed panel.
- Test a gate by breaking a task on purpose. Six injected defects, six catches; before the
  rewrite all four tasks passed while three had been bounced by the platform.

---

### 2026-08-02 — miniob PR#69 (oceanbase buffer-pool / B+tree refactor)

**Task:** `tasks/active/a9a7c19a-a3c1-4e42-aaae-19df47c2935d_submission` — miniob PR #69

**Steps run:** 0 → 1 → 2 → 3 → 4

**Outcome:** Fixable — upload-ready zip at `tasks/out/a9a7c19a-a3c1-4e42-aaae-19df47c2935d_submission.zip` (13 f2p, oracle 1.0 / NOP 0.0)

**Issues fixed:**
- f2p was 5 (static check needs 10–20) → split unitest into 13 granular gtest cases
- `tests.patch` corrupt/truncated (missing `lower_bound_test.cpp`, wrong `@@` line count)
- BinaryIterator test used `begin+2` / single-deref — golden returns `T*` from `operator*`
- Verifier needed `rm -rf build` after golden moves `record_manager` (stale cmake cache)
- Stray tracked `.swp` + untracked `deps/3rd/` → git hygiene commit + `.gitignore`; updated `base_commit_sha`

**Rule for next time:** After editing patch `@@` hunks for new files, apply locally and `wc -l` the result; C++ refactor tasks that move sources need clean rebuild in `config.json execution.commands`.

---

### 2026-08-02 — Remove Playwright hub scraper scripts

**Steps run:** Delete playwright scripts; keep `docs/hub-scrape/`

**Outcome:** Repo has static hub docs only — no Playwright dependency

**Removed:** `hub-login-email.mjs`, `hub-login.mjs`, `fetch-hub.mjs`, `hub-explore-login.mjs`, `HUB-SYNC.md`

**Rule for next time:** Official hub updates → paste or re-export into `docs/hub-scrape/` manually; diff against condensed docs.

---

### 2026-08-02 — Hub doc alignment (full repo audit)

**Steps run:** Hub scrape audit → docs/scripts/templates alignment

**Outcome:** Repo aligned with official Sentinel Ultra Hub (Jul 2026)

**What changed:** `validate_task.py` enforces f2p 10–20; new `PLATFORM-TRIAGE.md`, `REVIEWER-GUIDE.md`, `HUB-SYNC.md`; expanded `GUIDELINES.md` (environment/git tables); unified 10–20 wording across all docs; Valid-as-is oracle/NOP requirement; Invalid form dirty-git sub-issue; QC >3.0 vs 4+ EC margin clarified; standing rules renumbered 14–24.

**Rule for next time:** Before claiming upload-ready, grep docs for stale "≥10" and run `validate_task.py --strict`.

---

### 2026-08-02 — Sentinel Ultra Hub scrape via Playwright

**Steps run:** Hub auth research → Playwright login → full doc scrape

**Outcome:** Success — hub docs saved locally under `docs/hub-scrape/`

**What happened:** User wanted agent access to gated [Sentinel Ultra Hub](https://snorkel-ai.github.io/Sentinel_Ultra_Hub/). Auth is client-side: approved emails are SHA-256 hashes embedded in the JS bundle (`function F6`); login sets `sessionStorage` key `sentinel-ultra-auth`. No OTP.

**Fix applied:** Added `scripts/hub-login-email.mjs` + `scripts/fetch-hub.mjs`. Scraped all tabs (Changelog requires `?changelog` query param to expose tab button). Session in `scripts/.hub-storage-state.json` (gitignored).

**Rule for next time:** Re-scrape with `HUB_EMAIL=… SENTINEL_REPO=$PWD node scripts/hub-login-email.mjs` from `/tmp/hub-fetch` (needs local `playwright` npm install). Changelog tab only visible with `?changelog` on first load.

---

### 2026-08-02 — agent-orchestrator S3 timeout fix (7f0d2832 re-zip)

**Steps run:** eval triage → fix packaging → re-zip

**Outcome:** Fixable — clean 23MB zip (was 255MB)

**What happened:** Snorkel S3 availability check timed out (AccessDenied/GuardDuty). Upload zip was 255MB / 41k files because `frontend/node_modules` (incl. Electron binary) was recreated during docker preflight and bundled; `zip -u` kept stale entries.

**Fix applied:** Removed node_modules; reset dirty repo; hardened `zip-task.sh` (fail on node_modules, dirty repo, zip >80MB; rm old zip first; hard validate gate).

**Rule for next time:** After `--docker` preflight, `rm -rf environment/repo/frontend/node_modules` before zip. Never upload without checking `ls -lh tasks/out/*.zip`.

---

### 2026-08-02 — opensandbox f2p count CI fix (dc0540bb)

**Steps run:** eval triage / fix / zip

**Task:** dc0540bb opensandbox PR183

**Outcome:** Fixable (revised) — 20 f2p, preflight PASS, zip re-created

**What happened:** CodeBuild `run_static_checks` failed: 21 f2p outside platform 10–20 range.

**Fix applied:** Removed `TestNewManagerWithOptions_ReturnsManager` from config + tests.patch (weakest test). 20 f2p remain.

**Rule for next time:** f2p must be 10–20 (standing rule 5b). Count before zip.

---

### 2026-08-02 — opensandbox PR183 eval triage + re-upload (dc0540bb)

**Steps run:** eval triage / fix / 3 / 4

**Task:** `tasks/active/dc0540bb-58c2-40e7-9595-2e382f08f6f8_submission/`

**Outcome:** Fixable (revised) — preflight PASS, zip re-created

**What happened (eval failures):**
- REMOVE overreach: test_faithfulness 2/5 — tests used hidden API names not in instruction
- 0/8 valid agent trials — harness failure: tests.patch conflicted when agents wrote manager_test.go / policy_server_test.go / edited policy_test.go
- We had **removed** "do not modify test files" thinking it was leakage — that caused the harness epidemic
- Oracle: retry returned original err not retry err; POST updated proxy before JSON response
- Packaging: server/.python-version shipped via COPY repo/

**Fix applied:**
- instruction: exact API names table + "do not write/modify *_test.go" + exact nft rule strings
- tests.patch → eval_*_test.go only (no patch to base policy_test.go); +3 coverage tests; 21 f2p, 3 p2p; allow_extra_failures=false
- golden.patch: retry returns retryErr; POST writes JSON then UpdatePolicy; CIDR Masked(); fixed hunk line count
- Dockerfile: delete .python-version after COPY

**Rule for next time:** See standing rules 14–18. Never trade test-hint removal for harness stability — phrase as agent constraint, not verifier spoiler.

---

### 2026-08-02 — opensandbox PR183 egress nftables (dc0540bb submission)

**Steps run:** 0 / 1 / 2 / 3 / 4

**Task:** `tasks/active/dc0540bb-58c2-40e7-9595-2e382f08f6f8_submission/` — opensandbox PR #183 (CIDR egress + nftables + policy server)

**Outcome:** Fixable (fixed) — preflight PASS, zip created

**What happened:**
- 18 f2p tests, golden.patch 724 lines matches PR #183 scope; pass_at_k 0/3 both models — appropriately hard
- Ingested zip had git hygiene failures: executable bit stripped on ~25 shell scripts, reflog present, stray tmp/ + SDK untracked files
- Instruction had test-hint line ("Do not modify test files") and untested main.go env/fail-fast requirements

**Fix applied:**
- Git hygiene: checkout -- ., clean -fd, remove .git/logs
- instruction.md: removed test hint + untested main.go wiring; synced problem_statement

**Rule for next time:**
- Zip ingest on macOS often strips +x from shell scripts → git checkout -- . fixes mode-only dirt
- Mount repo :ro in manual oracle docker runs — RW mount applies golden.patch to host repo
- Trim instruction requirements that have no enforcing test (main.go env parsing) before QC

---

### 2026-08-02 — agent-orchestrator PR2185 eval triage + harness fix (7f0d2832)

**Steps run:** eval triage → fix → preflight → re-zip

**Task:** `tasks/active/7f0d2832-75ad-4bde-a511-e7a60b1bf187_submission/`

**Outcome:** Fixable (revised) — harness + QC coverage/faithfulness fixes

**What happened:**
- Agent Runner REMOVE (coverage_gap): tests in `frontend/src/main/*.test.ts` conflicted when agents created same paths; instruction said "existing tests" misled agents
- Harness failure: tests.patch adds files agents also create → patch fails "already exists"
- QC: opts.log required `supervisor-link:` prefix not in instruction; backoff/drain not tested

**Fix applied:**
- Moved verifier tests to `frontend/src/verifier/` + `vite.verifier.config.ts` (node env, no setupFiles)
- Removed setup.ts patch (agent overlap risk)
- Instruction: "do not add/modify test files"; document `supervisor-link:` log prefix; soften navigation
- Added backoff + drain f2p tests → 14 total

**Rule for next time:**
- Never place tests.patch new files at paths agents are told to implement or likely to create
- Never say "existing tests at X" when tests ship only via tests.patch at verify time
- Document exact log/output formats tests assert (faithfulness)

---

### 2026-08-02 — agent-orchestrator PR2185 (7f0d2832 submission)

**Steps run:** 0 / 1 / 2 / 3 / 4

**Task:** `tasks/active/7f0d2832-75ad-4bde-a511-e7a60b1bf187_submission/` — AgentWrapper/agent-orchestrator PR #2185 (daemon supervisor link frontend)

**Outcome:** Fixable (fixed) — preflight PASS, zip created

**What happened:**
- Original zip had 8 f2p (need ≥10), wrong network_mode in task.toml, bundled frontend/node_modules stray artifact, reflog in .git/logs
- Instruction scoped to frontend `daemon-owner.ts` + `supervisor-link.ts`; golden.patch is full PR (backend supervisor + session lifecycle + frontend modules) — oracle aligns with instruction's frontend ask
- pass_at_k 4/8 Opus, 6/8 GPT — not skip territory; tag originally_too_easy but agents don't pass 100%

**Fix applied:**
- task.toml: [environment] public, [agent] allowlist + hosts, [verifier] no-network
- Added 3 f2p tests (non-fatal connect, opts.log, dispose clears connected) → 11 total
- Removed stray frontend/node_modules; git reflog hygiene
- Fixed tests.patch hunk line count (corrupt patch at line 963)

**Rule for next time:**
- When editing tests.patch hunks manually, recount + lines or regenerate with git diff — wrong count → "corrupt patch"
- Ingested zips may ship node_modules despite .gitignore — delete before validate_task

---

### 2026-08-01 — casbin PR378 skipped (difficulty FAIL EASY)

**Steps run:** eval triage → skip decision

**Task:** casbin-node-casbin PR378 (8959a77b submission)

**Outcome:** skipped (not Fixable to MEDIUM+ without breaking QC/PR)

**What happened:**
- QC OK, oracle 3/3, nop 0/1
- Agent Runner: FAIL EASY — requires at least MEDIUM
- Opus 8/8, GPT-5.5 8/8 pass — EC fixes for QC/oracle made hardened 0/3 task too easy

**Fix applied:** none — skip recommended; added docs/SKIP-GUIDE.md

**Rule for next time:**
- After QC/oracle pass, check agent pass rate before more revisions
- If 100% agent pass + FAIL EASY, skip per SKIP-GUIDE unless user wants large scope expansion

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
