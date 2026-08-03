# Revision budget — spend zero if possible

Canonical for the revision budget and for how to iterate locally and on the platform. Other
docs summarise it; none of them get to state a different number.

**Workspace policy: a task gets at most 2 revision cycles.** After that the reviewer can
only Reject (the platform hides "Needs Revision" and shows a *Maximum Revisions Reached*
dialog), and repeat revisions drag the Submission Quality Score toward 1–2.

The hub documents that a cap exists but never names the number — the 2 comes from our
project terms, so treat it as the binding constraint even though you will not find it in
`docs/hub-scrape/`.

## The distinction that matters

| Loop | Cost | Limit |
|------|------|-------|
| Platform evals with **Send to reviewer unchecked** | free | run as many as you need |
| A reviewer sending the task back | **one revision** | 2 |

The hub is explicit: *"Re-upload and re-run with Send to reviewer unchecked. Repeat until
checks pass, then check Send to reviewer and submit."* Eval iterations are not revisions.
Almost every burned revision comes from checking that box too early.

So the rule is simple: **converge locally, then converge on the platform, and only then
send to a reviewer.**

## Order of operations

1. **Local gate.** `./scripts/preflight.sh tasks/active/<name>` — structure, git, docker
   build, oracle 1.0, NOP 0.0. Zero failures. Read every warning and either fix it or be
   able to defend it in Comments for Reviewer.
2. **Local rubric.** `./scripts/preflight.sh tasks/active/<name> --rubric` — the Harbor
   rubric judge, the closest local stand-in for the blocking Quality Check. Fix what it
   cites before you upload.
3. **Upload with Send to reviewer UNCHECKED.** Run Static → Oracle → Difficulty → Quality.
4. **Triage each failure** against `PLATFORM-TRIAGE.md` before touching the task. An infra
   flake fixed by "rework" costs you a real revision later.
5. **Re-upload and re-run** until every check is green. Still unchecked.
6. **Then** check Send to reviewer, with the form filled from `templates/submission-notes.md`.

If the checks will not go green and the only remaining fixes would reduce PR scope, stop:
that is Not Fixable. If difficulty will not clear without breaking Quality Check, see
`SKIP-GUIDE.md`. Skipping costs nothing; a rejected submission costs reputation.

## What actually triggers Needs Revision

Reviewer error categories, in rough order of how often they bite, with the local check that
would have caught each one:

| Category | Caught locally by |
|----------|-------------------|
| Test ↔ Instruction Misalignment | the coverage/faithfulness map in Step 3, `--rubric` |
| Test Coverage Issues | `validate_task.py` f2p count + your requirement map |
| Instruction Prescriptiveness / Styling | `validate_task.py` leakage checks, `--rubric` |
| Exposing Hints/Answers | `validate_task.py` leakage checks |
| Oracle Solution Issues | oracle trial reward 1.0 |
| Test Build Issues | oracle/NOP trials, `git apply --check` |
| Metadata Issues | `validate_task.py` task.toml limits |
| Agent Timeout | `[agent] timeout_sec` at the 7200 ceiling |
| Environment / Pinning | docker build, pinned base image |
| PR Scope Violation | your own PR diff read — nothing automates this |
| Time-Based Tests | grep the patch for clocks and dates |

`PR Scope Violation` and `Test ↔ Instruction Misalignment` are the two no script can
decide for you. Spend your review time there.

## Before you check Send to reviewer

- [ ] `preflight.sh` clean, including oracle 1.0 and NOP 0.0
- [ ] Every platform check green on the current upload
- [ ] Every instruction requirement maps to at least one assertion, and back
- [ ] `golden.patch` is the source PR (plus additions only — never less)
- [ ] Warnings from the local gate are fixed or explained in Comments for Reviewer
- [ ] Form matches the verdict path (8 confirmations for Fixable, 7 for Valid-as-is)
- [ ] Comments for Reviewer names your judgment calls — reviewers must acknowledge them,
      and an explained edge case rarely comes back as a revision

## If a revision does come back

1. Read the reviewer's notes and error categories literally; fix exactly what is cited.
2. Re-run the full local gate — a fix in one place routinely breaks the oracle.
3. Answer the reviewer in Comments for Reviewer: what you changed and why. They are
   required to read it and to state whether it changed their outcome.
4. Log it in `EC-LEARNINGS.md`, and promote it to a standing rule if it could recur.

With one revision already spent, the second upload must be final. Re-audit the whole task,
not only the cited defect.
