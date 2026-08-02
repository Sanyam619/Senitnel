# Platform triage — eval failures vs task defects

When Snorkel evals fail or return confusing output, classify the failure **before** rewriting
the task or marking it Not Fixable. Official hub FAQ (Jul 2026).

## Infra/platform failures (NOT a task defect)

**Do not** mark Unfixable. **Do not** burn a revision slot resubmitting an unchanged zip.

| Symptom | Examples |
|---------|----------|
| Rate limits / sandbox | `DaytonaRateLimitError`, `ApiRateLimitError`, sandbox auth/connection errors |
| Intermittent agent exit | One-off `NonZeroAgentExitCode` while other runs pass |
| Missing eval output | Blank feedback, "No evaluation information available" |

**Tell:** Same task passes on one run and errors on another; only 1 of N agent runs fails.

**What to do:**
1. Retry later — most clear on their own.
2. Check status: `stb submissions list` (CLI is source of truth if GUI lags).
3. If persistent: flag on Slack with task/submission UID + exact error + whether intermittent.
4. Keep fixing the task only if you find a **reproducible** defect in task files.

## Harness failures (task defect — fix locally first)

These reproduce identically every run. Resubmitting unchanged zip always fails the same way.

| Symptom | Fix |
|---------|-----|
| `tests.patch` won't apply | Regenerate from base commit; see `TASKING-GUIDE.md` |
| 0/8 valid trials — infra/harness | Usually patch apply, git hygiene, or packaging |
| Static check: f2p count | Must be **10–20** in `config.json` |
| Packaging axis cap at 1 | Stray artifacts (`node_modules`, `__pycache__`, `.DS_Store`, etc.) |

## Agent nonzero exit code

After usual troubleshooting (local Docker build, patch applies to base, raise `[agent] timeout_sec` up to **7200**):

1. Try **removing `curl`** from `environment/Dockerfile` package installs and rebuild.
   Known Harbor edge-case bug; affects a small subset of tasks.
2. If task genuinely needs `curl`, or removal doesn't help → flag UID on Slack.

## Difficulty linter conflict (known issue)

If linter rejects task as "easy" after a difficulty downgrade:

- **Do not** hand-edit pass-rate/difficulty fields in `task.toml` to fight the linter.
- Flag on Slack with UID + the two conflicting values (linter floor vs measured metadata).
- This is a tooling gap — not something you resolve by tweaking the task alone.

See also `docs/SKIP-GUIDE.md` for when to **Skip** (FAIL EASY + ~100% agent pass).

## Submission status

```bash
stb submissions list
```

Use when GUI flickers or disagrees with actual pipeline state.

## Send to reviewer timing

Platform eval button has a **~5 minute** limit. For Fixable tasks, run evals and iterate
**before** checking Send to reviewer on final submit.
