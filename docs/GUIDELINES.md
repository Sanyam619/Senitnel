# Sentinel Guidelines (condensed)

Official Snorkel Sentinel Ultra contributor rules — aligned with hub docs (Jul 2026).
Full reference: `docs/hub-scrape/` (static copy of the official hub).

## Purpose

Build a high-quality dataset of **Harbor-format software-engineering tasks** from real
open-source PRs. Every task must be **correct, complete, and impossible to game**.

## Four core principles

| # | Principle | Check |
|---|-----------|-------|
| 1 | **Solvable** | Competent engineer can solve from instruction alone; only references real repo artifacts |
| 2 | **Clarity & no leakage** | Describes problem + behavior, not implementation; no PR URLs, spoilers, or test hints |
| 3 | **Verifiable** | **10–20** outcome-based fail-to-pass tests; regression guard; deterministic; not gameable |
| 4 | **Authentic** | Real engineering ask (~100+ lines, 2+ files); matches source PR scope |

## Verdicts

### Valid as-is
Instruction, tests, and oracle align with source PR. **Run oracle + NOP locally before
submit** — platform does not re-run difficulty evals on Valid as-is.

### Fixable
Issues in instruction, tests, oracle, allowed Dockerfile fixes, or git hygiene — you can
fix all of them.

Common fixable issues:
- Over-prescriptive or templated instruction
- Test gaps or grading undescribed behavior
- Fewer than 10 fail-to-pass tests (add to reach **10–20**)
- Solution leakage
- Oracle doesn't match instruction
- Fixable Dockerfile issues (see table below)
- Git hygiene (see `GIT-HYGIENE.md`)

### Not Fixable
- Only fix requires **reducing or replacing PR scope**
- Environment issues ECs cannot fix (see table below)
- **Dirty git history that can't be recovered** — rare; most git issues are fixable

## PR scope rules

**May:** Add complexity on top of original PR (more edge cases, robustness).

**May not:** Reduce scope, swap feature type, or replace with unrelated work.

## What you may edit

| Component | Allowed |
|-----------|---------|
| `instruction.md` | Yes — rewrite for clarity, no leakage |
| `environment/problem_statement.md` | Yes — must stay identical to instruction |
| `tests/tests.patch`, `config.json`, `test.sh` | Yes — add f2p tests, align with instruction |
| `solution/solve.sh`, `golden.patch` | Yes — fix oracle or expand PR scope |
| `environment/Dockerfile` | Limited fixes only (see below) |
| `environment/repo/` tracked files | **Never** |
| `environment/repo/` git metadata | Yes — hygiene fixes |

## Instruction rewrite — examples

| Bad (prescriptive) | Good (behavioral) |
|--------------------|-------------------|
| "Fix the range() call inside the list comprehension…" | "Generated slots must never extend past the schedule's availability end time." |
| "The hook should expose handleScrollContainerWheel because tests reference this name." | "The hook should expose a stable wheel handler for the scroll container." |
| "Where to look: helpers/queue.py, tests/test_foo.py" | Describe symptom and expected behavior only |

**Document required output formats** in instruction — that is not leakage.

**Personas:** casual/Slack, structured ticket, technical memo, prose/email, or acceptance
criteria — pick one and stay consistent.

## Test requirements

- **10–20 fail-to-pass** in `tests/config.json` (platform static check rejects >20)
- Outcome-based: run code, check behavior — not diff structure or source keywords
- At least one test reproduces the original failure (fails pre-patch, passes post-patch)
- Deterministic: fixed seeds, no flaky/order-dependent behavior
- Pass-to-pass tests must stay **byte-identical** to base commit — add new tests only
- Names in tests must be **derivable** from instruction or existing codebase

### Derivable names
OK if: already in codebase, standard convention, or explicitly stated in instruction.

## Fixable Dockerfile / environment issues

| Issue | Fix |
|-------|-----|
| Alpine missing bash | `apk add --no-cache bash` (autocorrect: alpinebashautocorrect) |
| Missing `environment/frozen-requirements.txt` when Dockerfile COPYs it | Generate file (autocorrect: frozenrequirementsautocorrect) |
| `tmux` not installed | Harbor needs tmux for agent session — apt/apk install |
| `asciinema` not installed | Required for terminal recording — install in image |
| Unpinned `:latest` base image | Pin concrete tag |
| Resource limits too low / OOM | Bump cpus/memory in `task.toml` within limits |
| Bad shebang / CRLF / non-executable scripts | Fix in Dockerfile or scripts |
| Build reproducibility | `apt-get update` before installs; bake test deps into image |

Build **may** use network; **run-time** sandbox restricts agent to model gateway; verifier airgapped.

## Not fixable environment issues

| Issue | Why |
|-------|-----|
| Tangled apt/pip/cargo install failures | Cannot reliably fix without replacing toolchain |
| External-network dependency at **solve** time | Agent cannot reach required live services |
| Multi-GB model pulls or live external services | Not vendorable in allowed fixes |
| Oracle timeout after max timeout bump | If only fix is reducing PR scope → Not Fixable |

For oracle timeout: try raising `[agent]` / verifier timeouts within limits first.

## Git — fixable in the repo

Inside `environment/repo/` only (never edit tracked source):

| Issue | Fix |
|-------|-----|
| HEAD ≠ `base_commit_sha` in task.toml | Realign repo to base; update task.toml to match HEAD |
| Commits after base / leaked fix history | Reset to base commit |
| Remotes, stray branches/tags | Remove |
| Reflog present | Strip `.git/logs` |
| `.git/` > 100 MB | `git gc`, remove bloat |
| `filter.*` drivers | Remove from git config |

Run `./scripts/git-hygiene.sh` before every zip.

## Difficulty

Tasks should be genuinely hard. If fixing issues made it too easy, **expand PR scope**
(not vague requirements or unrelated stapled changes). Platform difficulty evals catch this.

If Difficulty FAIL EASY after QC/oracle OK → see `SKIP-GUIDE.md`.

## Network (task.toml)

```
[environment] network_mode = "public"
[agent]       network_mode = "allowlist", allowed_hosts = ["api.portkey.ai"]
[verifier]    network_mode = "no-network"
```

Remove `network_mode = "none"` from `docker_compose.yaml` if present.

## Stray artifacts (packaging)

Before zip, sweep task directory — any hit hard-caps packaging score at 1:

```bash
find . -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' \
  -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \
  -o -name '.venv' -o -name 'node_modules' -o -name '.idea' -o -name '.vscode' \
  -o -name '*.swp' -o -name '*~' -o -name '*.orig' -o -name '*.bak'
```

Also: no solution material readable from agent paths in built image.
