# Sentinel Guidelines (condensed)

Official Snorkel Sentinel Ultra contributor rules — distilled for daily EC work.

## Purpose

Build a high-quality dataset of **Harbor-format software-engineering tasks** from real
open-source PRs. Every task must be **correct, complete, and impossible to game**.

## Four core principles

| # | Principle | Check |
|---|-----------|-------|
| 1 | **Solvable** | Competent engineer can solve from instruction alone; only references real repo artifacts |
| 2 | **Clarity & no leakage** | Describes problem + behavior, not implementation; no PR URLs, spoilers, or test hints |
| 3 | **Verifiable** | ≥10 outcome-based fail-to-pass tests; regression guard; deterministic; not gameable |
| 4 | **Authentic** | Real engineering ask (~100+ lines, 2+ files); matches source PR scope |

## Verdicts

### Valid as-is
Instruction, tests, and oracle align with source PR. **Run oracle + NOP locally** before
submit — platform does not re-run difficulty on Valid as-is.

### Fixable
Issues in instruction, tests, oracle, allowed Dockerfile fixes, or git hygiene — you can
fix all of them.

Common fixable issues:
- Over-prescriptive or templated instruction
- Test gaps or grading undescribed behavior
- Fewer than 10 fail-to-pass tests
- Solution leakage
- Oracle doesn't match instruction
- Fixable Dockerfile issues (missing bash/tmux, unpinned base image)
- Git hygiene (see `GIT-HYGIENE.md`)

### Not Fixable
- Only fix requires **reducing or replacing PR scope**
- Environment issues ECs cannot fix (tangled toolchain, external deps at solve time)

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

## Test requirements

- **≥10 fail-to-pass** (ideally 10–20)
- Outcome-based: run code, check behavior — not diff structure or source keywords
- At least one test reproduces the original failure (fails pre-patch, passes post-patch)
- Deterministic: fixed seeds, no flaky/order-dependent behavior
- Pass-to-pass tests must stay **byte-identical** to base commit — add new tests only
- Names in tests must be **derivable** from instruction or existing codebase

### Derivable names
OK if: already in codebase, standard convention, or explicitly stated in instruction.

## Fixable Dockerfile issues

- Missing bash on Alpine → `apk add bash`
- Missing tmux / asciinema (Harbor session)
- Unpinned `:latest` base image
- Resource limits too low
- Bad shebang / CRLF / non-executable scripts
- Missing `frozen-requirements.txt` when Dockerfile COPYs it

## Not fixable environment issues

- Tangled apt/pip/cargo install failures
- Oracle timeout (may try bumping timeout first)
- Multi-GB model pulls or live external services at solve time

## Difficulty

Tasks should be genuinely hard. If fixing issues made it too easy, **expand PR scope**
(not vague requirements or unrelated stapled changes). Platform difficulty evals catch this.

## Network (task.toml)

```
[environment] network_mode = "public"
[agent]       network_mode = "allowlist", allowed_hosts = ["api.portkey.ai"]
[verifier]    network_mode = "no-network"
```

Remove `network_mode = "none"` from `docker_compose.yaml` if present.

Build may use network; **run-time** agent reaches only model gateway; verifier airgapped.
