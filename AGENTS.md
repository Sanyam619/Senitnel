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
3. ≥10 fail-to-pass tests in `tests/config.json`.
4. Never modify pass-to-pass files at base — add via `tests/tests.patch` only.
5. After instruction edits: `./scripts/sync-problem-statement.sh tasks/active/<name>`.
6. Before upload: `./scripts/preflight.sh tasks/active/<name> --docker`.
7. Zip: `./scripts/zip-task.sh tasks/active/<name>` → `tasks/out/<name>.zip`.
8. Instruction = behavior + success criteria, not implementation plan.
9. Tests ↔ instruction aligned both ways (Quality Check blocks gaps).
10. Oracle matches instruction; golden.patch matches PR (+ allowed expansion).

## Commands

```bash
./scripts/ingest-task.sh <zip-in-inbox>
./scripts/sync-problem-statement.sh tasks/active/<name>
./scripts/preflight.sh tasks/active/<name> [--docker] [--harbor]
./scripts/zip-task.sh tasks/active/<name>
python3 scripts/validate_task.py tasks/active/<name>
```

## Read first

- `docs/EC-LEARNINGS.md` — standing rules + session log (read at start; append at end of every session)
- `docs/SENTINEL-PROMPTS.md` — agent playbook (user says "I added foo.zip")
- `docs/QUALITY-CHECK.md` — blocking judge rules
- `docs/EC-REVIEW-CHECKLIST.md` — review checklist

This repo is Sentinel-only — not TB3/TERMINUS authoring.
