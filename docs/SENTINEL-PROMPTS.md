# Sentinel EC — agent playbook

**For the user:** Drop a zip in `tasks/inbox/` and tell Cursor:

> I added `my-task.zip`

That is enough. The agent reads this file and runs the workflow below automatically.

**For the agent:** When the user adds a zip (or points at an active task), follow this file
end-to-end unless they say otherwise. Do not ask which step to run — execute Steps 0 → 1 → 2 → 3 → 4
in order, stopping only on Not Fixable or when the user interrupts.

**Learnings (mandatory):** At session start read `docs/EC-LEARNINGS.md` (Standing rules + last 5
entries). At session end append a log entry there — **without the user asking**. Promote repeated
mistakes to Standing rules.

---

## Paths

| Folder | Purpose |
|--------|---------|
| `tasks/inbox/` | User drops downloaded Snorkel zips here |
| `tasks/active/<name>/` | Unpacked task you edit |
| `tasks/out/<name>.zip` | Upload to Snorkel |

Always read first: `docs/EC-LEARNINGS.md` (standing rules), `AGENTS.md`, `docs/GUIDELINES.md`,
`docs/EC-REVIEW-CHECKLIST.md`, `docs/QUALITY-CHECK.md`, `docs/HARBOR-FORMAT.md`, `docs/GIT-HYGIENE.md`.

---

## Hard rules (every step)

1. Never edit tracked files in `environment/repo/` (git metadata only).
2. ≥10 fail-to-pass tests in `tests/config.json`.
3. pass-to-pass files unchanged at base — add tests only via `tests/tests.patch`.
4. PR scope: expand OK; reduce/replace → **Not Fixable**.
5. After any `instruction.md` edit: `./scripts/sync-problem-statement.sh tasks/active/<name>`.
6. Instruction = behavior + success criteria, not an implementation plan.
7. Tests ↔ instruction aligned both ways (coverage + faithfulness).
8. Before upload: preflight PASS, then zip.

---

## Step 0 — Ingest

**Trigger:** User says they added a zip (or gives a filename in `tasks/inbox/`).

**Do:**
```bash
./scripts/ingest-task.sh <zip-filename>
```

Read the unpacked task under `tasks/active/` (and `tasks/active/<name>_runs/` if present).

**Do NOT edit files yet.**

**Report:**
1. Active folder path
2. Whether `runs/` exists — one-line summary of agent failures/timeouts if so
3. Sanity: `instruction.md`, `task.toml`, `environment/repo/.git`, `tests/config.json`,
   `tests/tests.patch`, `solution/golden.patch`, `environment/Dockerfile` all present?
4. Fail-to-pass count from `config.json` (need ≥10)
5. Source PR URL from `task.toml` `[metadata].source`
6. **Continue to Step 1** OR list blockers (corrupt zip, missing repo, patch won't apply)

---

## Step 1 — First read (no edits)

**Trigger:** Automatically after Step 0, or user says "review the active task".

**Do NOT edit any files. Do NOT edit tracked source in `environment/repo/`.**

Read the active task: `instruction.md`, `task.toml`, `environment/Dockerfile`, skim `environment/repo/`,
`tests/config.json`, `tests/tests.patch`, `tests/test.sh`, `solution/golden.patch`, `solution/solve.sh`,
`runs/` if present.

**Deliver:**

### Verdict
`Valid as-is` | `Fixable` | `Not Fixable` — one sentence why.

If **Not Fixable**, cite the specific rule from `docs/GUIDELINES.md` and **stop**.

### PR anchor
Source PR vs what instruction + `golden.patch` implement. Scope expansion present or needed?

### Four principles (pass/fail + one-line evidence each)
1. Solvable
2. Clarity & no leakage
3. Verifiable (≥10 f2p, outcome-based, deterministic)
4. Authentic (~100+ lines, 2+ files, real engineering ask)

### Issue list
Numbered, file refs, tagged: `Instructions` | `Tests` | `Oracle` | `Dockerfile` | `Git` | `Metadata`

### Test inventory
- f2p count vs minimum 10
- p2p count
- skip / skipif / fail-open / exists-only / overreach patterns?

### Quality Check risks
Coverage gaps, faithfulness gaps, prescriptive instruction, solution leakage.

### Runs insights
Common agent failure modes if `runs/` exists.

### Next step
- **Valid as-is** → skip Step 2, go to Step 3
- **Fixable** → continue to Step 2
- **Not Fixable** → stop

---

## Step 2 — Fix the task

**Trigger:** Verdict is Fixable (automatic), or user says "fix it".

Fix everything needed for Snorkel **Accept**. Work in `tasks/active/<name>/`.

**Fix as needed:**
- `instruction.md` — behavioral, no leakage, document output schemas tests assert
- `environment/problem_statement.md` — synced via script after instruction edits
- `tests/tests.patch`, `tests/config.json`, `tests/test.sh`
- `solution/golden.patch`, `solution/solve.sh`
- `environment/Dockerfile`, `task.toml`, git hygiene

**When adding tests:**
- Hard cases: reasoning errors, missed edge cases, boundary conditions
- At least one regression test (fail pre-patch, pass post-patch)
- Fixed seeds, deterministic, no network dependence
- Outcome-based only — no source keyword scans, no silent skips, no fail-open
- Every assertion grounded in instruction or derivable from codebase

**Do NOT zip yet.**

**Report:**
1. Every file changed (path + what + why)
2. New f2p count
3. Coverage map: instruction requirement → test(s)
4. Faithfulness map: assertion → instruction grounding
5. PR scope expansion (or "NA")
6. **Continue to Step 3**

---

## Step 3 — Pre-upload gate

**Trigger:** Automatically after Step 2 (or after Step 1 if Valid as-is).

### Part A — Manual audit
1. List every requirement sentence in `instruction.md`
2. For each: name the test(s) that enforce it
3. List every assertion in patched tests
4. For each: cite instruction grounding
5. Grep tests for: `skip`, `skipif`, `importorskip`, bare `exists()`, fail-open patterns

### Part B — Scripts (fix and re-run until PASS)
```bash
./scripts/sync-problem-statement.sh tasks/active/<name>
./scripts/preflight.sh tasks/active/<name> --docker
```
Add `--harbor` if harbor CLI is available.

### Part C — Oracle/NOP (if harbor ran)
- Oracle reward = 1.0?
- NOP reward = 0.0?

**Report:** `READY FOR UPLOAD` yes/no. If no, exact blockers with file refs.

If ready → **continue to Step 4**.

---

## Step 4 — Zip + submission form

**Trigger:** Step 3 reports ready (automatic), or user says "zip it".

```bash
./scripts/zip-task.sh tasks/active/<name>
```

Confirm output at `tasks/out/<name>.zip`.

Write copy-paste Snorkel platform form content (plain engineer tone). Use
`templates/submission-notes.md`. **Form fields depend on verdict** — Fixable has the full form.

### If verdict is Fixable — output ALL of these (separate fenced code blocks):

1. **Verdict** — Fixable (pick same twice on form)
2. **Where issues were** — which checkboxes: Instructions / Tests / Oracle / Environment
3. **What issue types** — which checkboxes apply (only issues that were present before fix)
4. **Describe each issue in detail** — numbered format with Fixable + Fix per issue
5. **Files changed** — table (path | what | why)
6. **PR modification details** — expansion explanation or NA
7. **8 confirmation checkboxes** — list all 8; agent confirms each is true after fixes
8. **What makes this task difficult?**
9. **Senior engineer time** — <10 | 10-20 | 20-40 | 40+ minutes
10. **Comments for Reviewer** — assumptions, judgment calls (not full repeat of issues/files)
11. **Four time fields (minutes):** review validity | initial rewrite | form questions | all revisions
12. **Zip path** — `tasks/out/<name>.zip` to upload (twice if form asks: initial + re-upload)

### If verdict is Invalid/Not Fixable — output ALL of these (separate fenced code blocks):

1. **Verdict** — Invalid/Not Fixable (pick same twice)
2. **Issue checkboxes** — PR scope change/reduction and/or Environment Issues
3. **Environment sub-issues** — if Environment checked: build failures / oracle timeout / external network
4. **Why unfixable (required)** — detailed explanation with GUIDELINES citation and evidence
5. **Optional upload note** — what to include if uploading investigation zip
6. **What makes this task difficult?**
7. **Senior engineer time** — <10 | 10-20 | 20-40 | 40+ minutes
8. **Comments for Reviewer**
9. **Two time fields (minutes):** review validity | all revisions
10. **No corrected zip upload** — unless optional reviewer verification

### If verdict is Valid-as-is — output ALL of these (separate fenced code blocks):

1. **Verdict** — Valid-as-is (pick same twice)
2. **7 confirmation checkboxes** — list all 7; agent confirms each is true after Step 1 review
3. **What makes this task difficult?**
4. **Senior engineer time** — <10 | 10-20 | 20-40 | 40+ minutes
5. **Comments for Reviewer** — optional context
6. **Two time fields (minutes):** review validity | all revisions (often 0 revisions)
7. **Zip note** — upload original unchanged zip if form requires; no corrected re-upload

Also print the internal pre-submit checklist (not pasted into form).

Tell the user to upload `tasks/out/<name>.zip` to Snorkel and run evals.

Then **append a session log entry to `docs/EC-LEARNINGS.md`** (see template there).

---

## If this happens… (conditional branches)

Use these **instead of or after** the main steps when the situation matches.
Do not run all branches every time.

### If instruction is the main problem (prescriptive, leaky, LLM voice)
**When:** Step 1 flags instruction issues but tests/oracle are mostly fine.

Rewrite `instruction.md` only:
- Real ticket/memo voice — not robotic template
- Symptoms + expected behavior, not where to edit or how to implement
- Document output schema if tests assert format
- No PR links, spoilers, test hints, verifier internals
- References only artifacts in `environment/repo/`

Run sync-problem-statement. Re-check coverage/faithfulness. Continue Step 3.

---

### If tests are the main problem (coverage / faithfulness / Quality Check)
**When:** Step 1 or platform eval flags test gaps, overreach, skips, or fail-open patterns.

Work on `tests/` only:
- ≥10 f2p in `config.json`
- Every instruction requirement → ≥1 assertion
- Every assertion → instruction or derivable name
- Hard edge cases, not trivial exists/touch checks
- Regenerate `tests.patch` from base commit if test files changed

Update `config.json` f2p list. Continue Step 3.

---

### If oracle is the main problem (golden.patch misaligned)
**When:** Tests/instruction changed, or Step 1 flags oracle ≠ instruction/PR.

Verify and fix `solution/golden.patch` + `solve.sh`:
- Implements what instruction asks (not a different fix)
- Matches source PR scope (+ documented expansion only)
- ~100+ lines, 2+ files, no unrelated refactors
- Applies cleanly on base commit → reward 1.0

Never edit tracked repo files directly. Continue Step 3.

---

### If platform eval fails after upload
**When:** User pastes Snorkel eval / Quality Check output.

For each failure:
1. Quote exact failure message
2. Root cause in task files (cite path)
3. Minimal fix
4. Classify: coverage | faithfulness | oracle | difficulty | static | packaging

Apply fixes. Re-sync problem_statement if instruction changed.
Re-run preflight `--docker`. Re-zip (Step 4). Summarize re-upload steps.

---

### If form asks for difficulty / solution / verification blurbs
**When:** Snorkel submission form needs the three explanation fields.

Read instruction, tests, solution. Write exactly:

**Difficulty Explanation** — must start with: `This task is hard because`
**Solution Explanation** — overall approach, main idea
**Verification Explanation** — must start with: `The tests checks`

Each section 2–3 lines. Informal engineer tone. Based on what the task actually tests.
No file names or code paths unless absolutely necessary.

---

### If user wants everything in one pass (skip step-by-step reports)
**When:** User says "just do it" or "one-shot" on a task they trust is fixable.

Run Steps 0 → 1 → 2 → 3 → 4 with minimal intermediate reporting.
Stop immediately if Not Fixable. Report final summary only: verdict, files changed,
f2p count, upload-ready, zip path.

---

## User cheat sheet

| You do | Agent does (this file) |
|--------|-------------------------|
| Download zip from Snorkel | |
| Copy zip → `tasks/inbox/` | |
| **"I added foo.zip"** | Steps 0 → 1 → 2 → 3 → 4 automatically |
| Upload `tasks/out/foo.zip` | |
| Run evals on Snorkel | |
| Paste eval error | "If platform eval fails" branch |
| Need difficulty blurbs | "If form asks for difficulty" branch |

**Optional overrides** (say any time):
- `"Step 1 only"` — review, no edits
- `"Skip to Step 3"` — task already fixed
- `"Fix tests only"` — tests branch
- `"One-shot"` — all steps, minimal chatter

---

## Session end — always log (agent)

**Trigger:** Any Sentinel session ending — full workflow, partial work, Not Fixable stop, eval
triage, or user interrupt. User does not need to ask.

**Do:** Append entry to `docs/EC-LEARNINGS.md` Session log (newest first). Include:
- Task name / path
- Steps run
- Outcome
- What went well, mistakes, fixes
- **Rule for next time** (one line)

If the rule applies to all future tasks, also add/update **Standing rules** table.
