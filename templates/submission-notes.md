# Snorkel submission form — copy-paste guide

Matches **Sentinel 2.0 Submission** form (verified 2026-07-29).

**Left panel** is read-only (directory name, category, tags, metadata). Everything below is **right panel**.

The form **changes based on verdict**. Three paths:

- **Path A — Fixable** (most common for EC work)
- **Path B — Invalid/Not Fixable**
- **Path C — Valid-as-is**

---

## Path A — Fixable (full form)

### Section 1 — Submitter Questions

#### 1. Upload zip (required)

Upload flat zip from `tasks/out/<task-name>.zip` after preflight PASS.

Do **not** include `runs/` or wrap in a `task/` folder.

---

#### 2. Verdict — pick TWICE, same choice

**Field A:** `(SEGMENTS)` → Fixable / Invalid / Valid-as-is  
**Field B:** `[Duplicate]` → must match Field A

Pick **Fixable** when issues are in instruction, tests, and/or oracle and you fixed all of them.

---

#### 3. Select where the task had issues (checkboxes — all that apply)

Check every area you touched:

- [ ] **Instructions**
- [ ] **Tests**
- [ ] **Oracle Solution**
- [ ] **Environment/Dockerfile**

---

#### 4. What issues did you find? (checkboxes — all that apply)

Check only issues that were **actually present** before your fix:

- [ ] Every requirement in the instructions is not properly tested
- [ ] All test requirements are not properly specified in the instructions
- [ ] The instructions appear LLM generated
- [ ] The instructions are overly-prescriptive
- [ ] The task leaks solution information
- [ ] The oracle does not implement the solution following the instructions
- [ ] Less than 10 fail-to-pass tests in test suite

---

#### 5. Describe each issue in detail (text box)

Use this format for **each checked issue above**:

```
1) [Instructions] — <specific issue with examples from instruction/tests>
   — Fixable: yes/no
   — Fix: <what you changed>

2) [Metadata] — <issue>
   — Fixable: yes/no
   — Fix: <what you changed>
```

Categories: Instructions | Tests | Oracle Solution | Environment/Dockerfile | Metadata

---

#### 6. Re-upload corrected zip (required for Fixable)

Upload the same `tasks/out/<task-name>.zip` (flat contents: instruction.md, task.toml, environment/, tests/, solution/).

---

### Section 2 — Additional Submitter Questions

#### 7. Files changed (text box)

```
| File | What changed | Why |
|------|--------------|-----|
| instruction.md | | |
| environment/problem_statement.md | synced from instruction | platform requirement |
| tests/tests.patch | | |
| tests/config.json | | |
| solution/golden.patch | | |
| environment/Dockerfile | | |
| task.toml | | |
```

Only list files you actually changed.

---

#### 8. PR Modification Details (text box)

Explain scope expansion, or write **NA** if golden.patch matches source PR only.

You may expand PR scope; you may not reduce or replace it.

---

#### 9. Task requirements confirmation (check ALL 8)

Only check these if true **after your fixes**:

- [ ] Every requirement in the instructions is properly tested
- [ ] All test requirements are properly specified in the instructions
- [ ] The instructions do not sound like an LLM generated them
- [ ] The instructions are not overly-prescriptive
- [ ] The task does not leak solution information
- [ ] The oracle implements the solution following the instructions
- [ ] The PR was not modified in any way beyond what is allowed by the guidelines
- [ ] More than 10 fail-to-pass tests in test suite

---

#### 10. What makes this task difficult? (text box)

Edge cases, dependencies, easy-to-miss requirements, test complexity. Not an implementation plan.

---

#### 11. Senior engineer solve time (one radio)

- [ ] <10 minutes
- [ ] 10-20 minutes
- [ ] 20-40 minutes
- [ ] 40+ minutes

---

### Section 3 — Final Comment and Handling Time

#### 12. Comments for Reviewer (text box)

Assumptions, edge cases, judgment calls, things not obvious from changed files.  
Do **not** repeat the full issue list or files table here unless adding context.

---

#### 13. Time fields (minutes — four separate boxes)

| Field | Meaning |
|-------|---------|
| Review initial task + determine validity | Step 1 |
| Initial task rewrite only | Instruction/oracle/test rewrite time |
| Additional questions on form | Time filling this form |
| All revisions | Total fix time; update on each resubmit |

---

## Path B — Invalid/Not Fixable

Use when fixing requires changing/reducing PR scope, editing tracked repo source, or
environment issues ECs cannot fix (see `docs/GUIDELINES.md`).

**Do NOT re-upload a corrected zip** unless optionally sharing work for reviewer verification.

### Section 1 — Submitter Questions

#### 1. Verdict — pick TWICE, same choice

**Invalid/Not Fixable** on both `(SEGMENTS)` and `[Duplicate]`.

---

#### 2. What issue did you find? (checkboxes — required)

Check all that apply:

- [ ] **PR scope needs to be changed or reduced**
- [ ] **Environment Issues**

---

#### 3. Environment sub-issues (optional — only if Environment Issues checked)

- [ ] Image/Dependency Build Failures
- [ ] Oracle timeout
- [ ] External-network dependency at build/solve time
- [ ] Dirty git history that can't be recovered (rare — most git issues are fixable per `GIT-HYGIENE.md`)

---

#### 4. Optional upload for reviewer

Upload optional zip with your investigation: partial fix attempt, eval logs, test output.
Reviewer verifies manually — not run through eval pipeline.

---

#### 5. Why unfixable — REQUIRED (text box)

Detailed explanation citing `docs/GUIDELINES.md`. Include:
- Source PR vs what task requires
- Why instruction/tests/oracle/Dockerfile/git cannot fix it
- Specific guideline rule (scope reduction, broken toolchain, etc.)

```
[Cite PR URL, base commit, and the blocking reason with evidence]
```

---

### Section 2 — Additional Submitter Questions

#### 6. What makes this task difficult? (text box)

Still required — describe technical complexity even though task is unfixable.

---

#### 7. Senior engineer time (one radio)

- [ ] <10 minutes
- [ ] 10-20 minutes
- [ ] 20-40 minutes
- [ ] 40+ minutes

---

### Section 3 — Final Comment and Handling Time

#### 8. Comments for Reviewer (text box)

Extra context: what you tried, eval failures, why you stopped, judgment calls.

---

#### 9. Time fields (minutes — two boxes)

| Field | Meaning |
|-------|---------|
| Review initial task + determine validity | Step 1 investigation time |
| All revisions | Any investigation/revision attempts |

(No "initial rewrite" or "form questions" fields on Invalid path.)

---

## Path C — Valid-as-is

Use when instruction, tests, and oracle already align — **no edits needed**.

### Section 1 — Submitter Questions

#### 1. Verdict — pick TWICE, same choice

**Valid-as-is** on both `(SEGMENTS)` and `[Duplicate]`.

---

#### 2. Confirm task complies (check ALL 7 — required)

Only check if true after your Step 1 review:

- [ ] Every requirement in the instructions is properly tested
- [ ] All test requirements are properly specified in the instructions
- [ ] The instructions do not sound like an LLM generated them
- [ ] The instructions are not overly-prescriptive
- [ ] The task does not leak solution information
- [ ] The oracle implements the solution following the instructions
- [ ] Contains more than 10 fail-to-pass tests in test suite

Note: Valid-as-is has **7** confirmations. Fixable has **8** (adds PR-not-modified-beyond-guidelines).

No issue checkboxes, no files-changed section, no re-upload of corrected task.

Upload the **original** task zip at the top if the form requires a file.

---

### Section 2 — Additional Submitter Questions

#### 3. What makes this task difficult? (text box)

Edge cases, dependencies, easy-to-miss requirements, test complexity.

---

#### 4. Senior engineer time (one radio)

- [ ] <10 minutes
- [ ] 10-20 minutes
- [ ] 20-40 minutes
- [ ] 40+ minutes

---

### Section 3 — Final Comment and Handling Time

#### 5. Comments for Reviewer (text box)

Optional context for reviewer — assumptions, edge cases, anything worth flagging.

---

#### 6. Time fields (minutes — two boxes)

| Field | Meaning |
|-------|---------|
| Review initial task + determine validity | Step 1 review time |
| All revisions | Usually 0 or minimal for Valid-as-is |

---

## Internal checklist (NOT on platform — verify before Submit)

- [ ] 11–20 fail-to-pass in config.json (the checkbox reads "More than 10")
- [ ] Coverage + faithfulness both directions
- [ ] problem_statement.md == instruction.md
- [ ] tests.patch applies to base commit
- [ ] Git hygiene clean
- [ ] preflight PASS including oracle 1.0 / NOP 0.0
- [ ] All platform checks green with Send to reviewer still unchecked
- [ ] Verdict matches twice
- [ ] Fixable: all 8 confirmation boxes honestly checked
- [ ] Invalid: cited GUIDELINES rule; no corrected zip required
- [ ] Valid-as-is: no unnecessary edits made
- [ ] Uploaded zip from tasks/out/ when Fixable (flat, no runs/)
