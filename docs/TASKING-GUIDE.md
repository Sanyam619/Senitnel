# Tasking Guide (condensed)

## Submission flow

1. Log in to **Snorkel Experts** → open Sentinel submission task
2. Download zip (`task/` + `runs/`)
3. Unpack `task/` locally → `./scripts/unpack-task.sh`
4. Review → verdict: Valid / Fixable / Not Fixable
5. If Fixable: rewrite instruction, tests, oracle as needed
6. `./scripts/sync-problem-statement.sh` after instruction edits
7. `./scripts/preflight.sh` — fix all failures
8. `./scripts/zip-task.sh` → upload flat zip (no `runs/`)
9. Run platform evals → iterate until pass
10. Check **Send to reviewer** → submit

**Throughput:** max 2 tasks in "pending revision" at once.

## Detailed review steps

### 1. Read instruction.md
- Requirements, expected behavior, success criteria
- Not overly prescriptive; no verifier internals

### 2. Cross-check source PR + task.toml
- Task reflects intended change
- Resources/timeouts within limits; `gpus = 0`
- Network blocks correct (see `HARBOR-FORMAT.md`)
- `source` URL matches PR

### 3. Scan environment
- Read `environment/Dockerfile`
- Skim `environment/repo/`
- `docker build environment/` locally

### 4. Review solution
- `solution/solve.sh` applies `golden.patch`
- Substantive change (~100+ lines, 2+ files)
- Oracle locally → reward **1.0**

### 5. Review tests
- `tests/tests.patch` = fail-to-pass tests
- `tests/config.json` = f2p / p2p lists + execution
- Count f2p: need **≥10**
- Every instruction requirement has a test
- Every assertion maps to instruction
- NOP locally → reward **0.0**

### 6. Review runs/ (reference only — do not upload)
- Timeouts, systematic misinterpretation, instability

### 7. Platform evals
Static → Oracle → Difficulty → **Quality Check** (blocking)

## Before You Upload checklist

Run `./scripts/preflight.sh <task-dir>` — it automates:

```bash
# tests.patch applies to base commit
cd environment/repo
git checkout <base_commit_sha>
git apply --check ../../tests/tests.patch

# Git hygiene (all must pass)
git rev-parse --verify HEAD
git rev-parse HEAD == base_commit_sha in task.toml
git rev-list --all --not HEAD    # empty
git remote                         # empty
git config --local --get-regexp '^filter\.'  # empty
git status --porcelain             # empty
ls .git/logs 2>/dev/null           # must not exist
du -sh .git                        # < 100 MB

# Stray artifacts sweep in task dir
# problem_statement.md == instruction.md
# Rename solution.patch → golden.patch if needed
# docker build environment/  (use --docker flag)
```

## Zip rules

```bash
cd <task-dir>
zip -rX ../out/my-task.zip . -x '*.DS_Store' '__MACOSX/*'
```

- Flat contents — unpacks to `instruction.md`, `task.toml`, `environment/`, etc.
- **Do not** use GUI compress or `zip -rD` (drops empty `.git/refs/` dirs)
- Verify: `unzip -l out/my-task.zip | grep 'refs/'`

## Platform form (Fixable)

Document each issue:
```
1) [Category] — specific issue with examples
   — Fixable? How?
2) [Category] — ...
```

List every file changed: path, what, why.

If expanded PR scope, explain how. Otherwise write "NA".

Confirm all requirement checkboxes before submit.

## Reviewer outcomes

| Outcome | Meaning |
|---------|---------|
| Accept | Accurate, complete submission |
| Needs Revision | Task still has fixable errors |
| Reject | Max revisions reached |

Target **submission quality score 4–5**.
