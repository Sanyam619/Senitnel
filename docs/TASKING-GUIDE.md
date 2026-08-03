# Tasking Guide (condensed)

## Submission flow

1. Log in to **Snorkel Experts** → open Sentinel submission task
2. Download zip (`task/` + `runs/`)
3. Unpack `task/` locally → `./scripts/ingest-task.sh <zip>`
4. Review → verdict: Valid / Fixable / Not Fixable
5. If Fixable: rewrite instruction, tests, oracle as needed
6. `./scripts/sync-problem-statement.sh` after instruction edits
7. `./scripts/preflight.sh <task>` — structure, git, docker build, oracle 1.0, NOP 0.0
8. `./scripts/zip-task.sh <task>` → upload flat zip (no `runs/`)
9. Run platform evals with **Send to reviewer unchecked** → iterate until all green
10. Only then check **Send to reviewer** → submit

**Throughput:** max 2 tasks in "pending revision" at once.

**Revision budget:** eval runs are free; reviewer round-trips are not. Read
`docs/REVISION-BUDGET.md` before step 9 — it is the difference between Accept and a
revision spiral.

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
- Count f2p: need **11–20** (see `GUIDELINES.md` for why 11)
- Every instruction requirement has a test
- Every assertion maps to instruction
- NOP locally → reward **0.0**

### 6. Review runs/ (reference only — do not upload)
- Timeouts, systematic misinterpretation, instability

### 7. Full local dry run

**Valid as-is (required):** oracle reward 1.0, NOP reward 0.0 — the platform does not re-run
difficulty evals on Valid-as-is, so your local run is the only check.

**Fixable (do it anyway):** the platform runs these on submit, but a local run saves an eval
round-trip — and a failed oracle after Send to reviewer costs a revision.

`preflight.sh` does both by default via the Harbor CLI:

```bash
./scripts/preflight.sh tasks/active/<task>            # + docker build + oracle + NOP
./scripts/preflight.sh tasks/active/<task> --rubric   # also run the rubric judge
./scripts/preflight.sh tasks/active/<task> --fast     # structure/git only, not a gate
```

Equivalent by hand:

```bash
docker build -t task-env environment/
harbor run -p <task> -a oracle   # reward 1.0
harbor run -p <task> -a nop      # reward 0.0 (f2p fail, p2p pass)
```

Mount the repo read-only in any manual docker run — a read-write mount applies
`golden.patch` to your working copy.

### 8. Platform evals
Static → Oracle → Difficulty → **Quality Check** (blocking)

## Before You Upload checklist

Run `./scripts/preflight.sh <task-dir>`. `zip-task.sh` then re-runs the structure and git
gates and refuses to build a zip that would fail them. Between them they automate:

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
./scripts/zip-task.sh tasks/active/<task>     # preferred — gated and verified
```

By hand:

```bash
cd <task-dir>
zip -rX ../out/my-task.zip . -x '*.DS_Store' '__MACOSX/*'
```

- Flat contents — unpacks to `instruction.md`, `task.toml`, `environment/`, etc.
- **Do not** use GUI compress or `zip -rD` (drops empty `.git/refs/` dirs)
- Verify: `unzip -l out/my-task.zip | grep 'refs/'`

`zip-task.sh` refuses to produce an archive when `runs/` is present, any stray artifact
exists, the repo is dirty, `validate_task.py` or `git-hygiene.sh` fail, the archive is not
flat, `refs/` entries are missing, or the zip exceeds 80 MiB.

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

Target **submission quality score 4–5**. Full reviewer playbook: `docs/REVIEWER-GUIDE.md`.

## Platform triage

When evals fail or return blank feedback, read `docs/PLATFORM-TRIAGE.md` before rewriting the task.
Use `stb submissions list` to check submission status.
