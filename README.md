# Sentinel — EC Workspace

Local home for **Sentinel Ultra** Expert Contributor work: review, fix, and submit
Harbor-format PR tasks on Snorkel Experts.

## Your workflow (simple)

```
1. Download zip from Snorkel Experts
2. Drop zip in tasks/inbox/
3. Tell Cursor: "I added foo.zip"
4. Cursor reads the playbook → reviews → fixes → preflight → zips → logs learnings
5. Upload tasks/out/foo.zip to Snorkel → run evals → submit
```

## Folder layout

```
sentinel/                    ← this repo (rename the folder anytime)
├── tasks/
│   ├── inbox/               ← YOU: drop every downloaded zip here
│   ├── active/              ← unpacked tasks (Cursor edits here)
│   └── out/                 ← upload zips for Snorkel
├── docs/                    ← guidelines + prompts
├── scripts/                 ← ingest, preflight, zip
└── AGENTS.md
```

## Manual commands (optional)

```bash
./scripts/ingest-task.sh my-task.zip          # inbox → active
./scripts/sync-problem-statement.sh tasks/active/my-task
./scripts/preflight.sh tasks/active/my-task --docker
./scripts/zip-task.sh tasks/active/my-task
```

## Before every upload

See `docs/EC-REVIEW-CHECKLIST.md` and `docs/SENTINEL-PROMPTS.md`.

## Docs

| File | Purpose |
|------|---------|
| `docs/SENTINEL-PROMPTS.md` | **Agent playbook — user says "I added foo.zip"** |
| `docs/EC-LEARNINGS.md` | **Standing rules + session log (agent reads/writes every time)** |
| `docs/GUIDELINES.md` | Four principles, verdicts, environment/git rules |
| `docs/TASKING-GUIDE.md` | Submission flow, before-upload checklist |
| `docs/HARBOR-FORMAT.md` | Task layout, task.toml, config.json |
| `docs/GIT-HYGIENE.md` | Git checks on `environment/repo/` |
| `docs/QUALITY-CHECK.md` | What blocks platform evals |
| `docs/PLATFORM-TRIAGE.md` | Infra vs task defects, CLI status, known issues |
| `docs/REVIEWER-GUIDE.md` | Reviewer outcomes and quality score |
| `docs/EC-REVIEW-CHECKLIST.md` | Review checklist |
| `docs/SKIP-GUIDE.md` | When to skip + Snorkel skip reason templates |
| `docs/hub-scrape/` | Static copy of official Sentinel Ultra Hub documentation |
| `templates/submission-notes.md` | Snorkel form copy-paste templates |
