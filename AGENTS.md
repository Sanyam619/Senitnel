# AGENTS.md — Sentinel EC workspace

Expert Contributor workspace for **Sentinel Ultra** on Snorkel Experts.

## Task folders

- `tasks/inbox/` — user drops downloaded zips here
- `tasks/active/` — unpacked tasks you edit
- `tasks/out/` — zips ready for Snorkel upload

When the user says they added a zip, run Step 0 from `docs/SENTINEL-PROMPTS.md`:
`./scripts/ingest-task.sh <zip-name>` then continue the prompt they requested.

## Must-fire rules

1. Never edit tracked source in `environment/repo/` (git metadata only).
2. PR scope: expand OK; never reduce or replace source PR.
3. **11–20** fail-to-pass tests in `tests/config.json`.
4. Never modify pass-to-pass files at base — add via `tests/tests.patch` only.
5. After instruction edits: `./scripts/sync-problem-statement.sh tasks/active/<name>`.
6. Before upload: `./scripts/preflight.sh tasks/active/<name>` — must be clean, including
   oracle 1.0 and NOP 0.0. Every WARN gets fixed or explained in Comments for Reviewer.
7. Zip: `./scripts/zip-task.sh tasks/active/<name>` → `tasks/out/<name>.zip`.
8. Instruction = behavior + success criteria, not implementation plan.
9. Tests ↔ instruction aligned both ways (Quality Check blocks gaps).
10. Oracle matches instruction; golden.patch matches PR (+ allowed expansion).
11. Never put `tests.patch` files at paths an agent may create — `eval_*` or verifier-only dir.
12. Revision budget is 2. Eval runs are free, reviewer round-trips are not: converge locally,
    then on the platform with Send to reviewer unchecked. See `docs/REVISION-BUDGET.md`.

## Commands

```bash
./scripts/ingest-task.sh <zip-in-inbox>
./scripts/sync-problem-statement.sh tasks/active/<name>
./scripts/preflight.sh tasks/active/<name>              # + docker build + oracle + NOP
./scripts/preflight.sh tasks/active/<name> --rubric      # local rubric judge
./scripts/preflight.sh tasks/active/<name> --fast        # mid-edit only, not a gate
./scripts/zip-task.sh tasks/active/<name>                # gated: refuses a bad zip
python3 scripts/validate_task.py tasks/active/<name>
python3 scripts/selftest.py                              # proves the validator still catches defects
python3 scripts/check-docs.py                            # docs vs tooling consistency
python3 scripts/fetch-hub-panels.py                      # refresh hub collapsible panels
```

## Where a rule lives

A rule may be summarised in several files, but it is *decided* in exactly one. Change it
there first; `scripts/check-docs.py` fails if a copy disagrees.

| Rule | Decided in |
|------|-----------|
| f2p range, PR scope, oracle edits, verifiability | `docs/GUIDELINES.md` |
| `task.toml` schema and resource limits | `docs/HARBOR-FORMAT.md` |
| Revision budget, local-vs-platform iteration | `docs/REVISION-BUDGET.md` |
| Eval failure triage (infra vs task) | `docs/PLATFORM-TRIAGE.md` |
| Skip criteria and wording | `docs/SKIP-GUIDE.md` |
| Enforced numbers (f2p, limits, network modes) | `scripts/validate_task.py` |

If a check and a doc disagree, the check wins — it is what actually gates the upload.

## Read first

- `docs/EC-LEARNINGS.md` — standing rules + session log (read at start; append at end)
- `docs/SENTINEL-PROMPTS.md` — agent playbook (user says "I added foo.zip")
- `docs/REVISION-BUDGET.md` — how not to spend a revision
- `docs/PLATFORM-TRIAGE.md` — infra vs task defects, eval triage
- `docs/SKIP-GUIDE.md` — when to skip + copy-paste Snorkel skip reasons
- `docs/QUALITY-CHECK.md` — blocking judge rules
- `docs/EC-REVIEW-CHECKLIST.md` — review checklist
- `docs/GUIDELINES.md`, `docs/HARBOR-FORMAT.md`, `docs/GIT-HYGIENE.md`
- `docs/hub-scrape/` — static copy of official Sentinel Ultra Hub docs
  (`guide-panels.txt` holds the collapsible panels the HTML scrape drops)

This repo is Sentinel-only — not TB3/TERMINUS authoring.
