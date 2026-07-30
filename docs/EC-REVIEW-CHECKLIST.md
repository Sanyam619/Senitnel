# EC review checklist — use on every task

Print or keep open while reviewing. Goal: **Accept** (quality score 4–5).

## Phase 1 — First read (15 min)

- [ ] Read `instruction.md` — does it read like a real ticket/memo/Slack ask?
- [ ] Open source PR from `task.toml` `[metadata].source` — same scope?
- [ ] Skim `runs/` if present — timeouts? systematic confusion?
- [ ] Verdict draft: Valid / Fixable / Not Fixable

## Phase 2 — Solvability & clarity

- [ ] Instruction references only things that exist in `environment/repo/`
- [ ] No "Where to look:", no test file names, no function names to edit
- [ ] Required output format/schema documented if tests assert it
- [ ] No PR URLs, commit SHAs, or solution spoilers in instruction
- [ ] Not robotic ("The system shall…") or identical template voice

## Phase 3 — Tests (most rejections happen here)

- [ ] Count fail-to-pass in `config.json` — **≥10**
- [ ] Map each instruction requirement → ≥1 test (coverage)
- [ ] Map each test assertion → instruction or derivable name (faithfulness)
- [ ] Regression test: reproduces original bug (fail pre-fix, pass post-fix)
- [ ] Outcome-based — not diff/keyword/source scans
- [ ] No skip/skipif/importorskip/fail-open patterns
- [ ] CLI/service tasks: tests actually invoke entry point
- [ ] Existence checks paired with content/behavior asserts
- [ ] pass-to-pass files unchanged from base (only additions via patch)

## Phase 4 — Oracle

- [ ] `golden.patch` implements instruction (not alternative invented fix)
- [ ] Matches source PR (+ documented expansion only)
- [ ] Substantive: ~100+ lines, 2+ files
- [ ] No unrelated refactors in patch
- [ ] Local oracle → reward **1.0**

## Phase 5 — Environment & packaging

- [ ] `task.toml` network blocks correct
- [ ] `gpus = 0`; timeouts within limits
- [ ] Dockerfile builds locally
- [ ] Base image pinned (not `:latest`)
- [ ] tmux/asciinema/bash present if needed
- [ ] No stray `__pycache__`, `.venv`, `.DS_Store` in task tree
- [ ] `problem_statement.md` == `instruction.md`

## Phase 6 — Git

- [ ] `./scripts/git-hygiene.sh` all PASS
- [ ] Did **not** edit tracked files in `environment/repo/`

## Phase 7 — Before upload

```bash
./scripts/ingest-task.sh <zip-in-inbox>
./scripts/sync-problem-statement.sh tasks/active/<task>
./scripts/preflight.sh tasks/active/<task> --docker
./scripts/zip-task.sh tasks/active/<task>
```

- [ ] Upload zip → run evals until all green
- [ ] Quality Check: test_coverage + test_faithfulness OK
- [ ] Fill submission form using `templates/submission-notes.md`

## Common fix patterns that get accepted

1. **Instruction** — replace file paths with behavior; add missing output schema
2. **Tests** — add f2p cases for each instruction bullet; remove overreach names
3. **Oracle** — align patch to instruction after test rewrite
4. **Dockerfile** — pin image, add tmux/bash, bump memory if OOM
5. **Git** — remove remotes/reflog/leaked commits; realign base_commit_sha

## When to mark Not Fixable

- Fixing requires shrinking or replacing PR scope
- Build/toolchain broken beyond allowed Dockerfile fixes
- External network required at solve time and cannot vendor
