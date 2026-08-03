# Sentinel Guidelines (condensed)

Official Snorkel Sentinel Ultra contributor rules — aligned with hub docs (Jul 2026).
Full reference: `docs/hub-scrape/` (static copy of the official hub). The tables below
come from the hub's collapsible panels, captured in `docs/hub-scrape/guide-panels.txt`
(regenerate with `python3 scripts/fetch-hub-panels.py`).

**Provenance:** everything here is hub-sourced except two items, flagged inline where they
appear — the **fail-to-pass upper bound of 20** and the **2-revision budget**. Both come
from our own experience, not the guidelines. Do not cite them to a reviewer as hub policy.

## Purpose

Build a high-quality dataset of **Harbor-format software-engineering tasks** from real
open-source PRs. Every task must be **correct, complete, and impossible to game**.

## Four core principles

| # | Principle | Check |
|---|-----------|-------|
| 1 | **Solvable** | Competent engineer can solve from instruction alone; only references real repo artifacts |
| 2 | **Clarity & no leakage** | Describes problem + behavior, not implementation; no PR URLs, spoilers, or test hints |
| 3 | **Verifiable** | **11–20** outcome-based fail-to-pass tests; regression guard; deterministic; not gameable |
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
- Too few fail-to-pass tests (add to reach **11–20**)
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

## Oracle — editable in exactly two cases

Edit `solve.sh` / `golden.patch` only to (1) correct an oracle that does not implement the
instruction, or (2) expand PR scope to raise difficulty. When you do:

- **Match the canonical fix** — the actual fix from the source PR, not an alternative you
  invented. Diverge only if the upstream fix is unavailable or unsuitable, and say why.
- **No unnecessary changes** — no unrelated refactors, style cleanups, or drive-by edits.
  (A solution that is *larger* than needed is acceptable if it does what the instruction
  requires and the tests enforce it — the oracle only has to prove solvability.)
- An expanded oracle must still resemble the source PR: anchor preserved, additions only.
- Update instruction and tests **in lockstep**, and keep the instruction reading as one
  realistic ask rather than a tacked-on list.
- After expanding scope, **re-run the difficulty eval** to confirm the task clears the bar.

If a fix would require reducing or replacing the PR's behavior, it is Not Fixable.

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

- **11–20 fail-to-pass** in `tests/config.json` — this file is where that range is
  decided; `scripts/validate_task.py` enforces it and `scripts/check-docs.py` fails if
  another document states a different one.
  - The hub guide says "at least 10, ideally 10–20". The platform confirmation checkbox
    reads "**More than** 10 fail-to-pass tests", so 11 is the honest floor. <!-- policy-check: ignore -->
  - The **20 ceiling is ours, not the hub's** — a CodeBuild `run_static_checks` run
    rejected a task at 21 f2p (`EC-LEARNINGS.md`, dc0540bb). The hub's "ideally 10–20"
    makes 20 safe regardless. <!-- policy-check: ignore -->
- Outcome-based: run code, check behavior — not patch structure, diff format, line numbers,
  file names, or source-code keyword matching; and not satisfiable by hardcoding
- At least one test reproduces the original failure (fails pre-patch, passes post-patch)
- Deterministic: fixed seeds, no flaky or order-dependent behavior, finishes in the timeout
- Independent of the oracle: never import or call the golden solution, and never compare
  against files only the solution creates. Bake fixtures into the verifier image
- Pass-to-pass tests must stay **byte-identical** to base commit — add new tests only
- Names in tests must be **derivable** from instruction or existing codebase

### Derivable names
A name is derivable only if it already exists in the base codebase, follows a standard
language/framework convention, or is explicitly stated in the instruction. Everything else
(function names, exact error strings, JSON keys, log formats, new file names, CLI flags)
must be written into the instruction or dropped from the tests.

To catch it: list the names the instruction specifies, scan the tests for expected names,
flag anything not derivable.

## Fixable Dockerfile / environment issues

| Issue | Fix |
|-------|-----|
| Alpine missing bash (scripts use a bash shebang, Alpine ships ash) | `apk add --no-cache bash` (autocorrect: alpinebashautocorrect) |
| Missing `environment/frozen-requirements.txt` when Dockerfile COPYs it | Generate file (autocorrect: frozenrequirementsautocorrect) |
| `tmux` not installed | Harbor drives agent/verifier in a tmux pane — no tmux, no session |
| `asciinema` not installed | Harbor records the terminal session — missing binary breaks the run |
| Unpinned `:latest` base image | Pin concrete tag |
| `DownloadVerifierDirError` / verifier-output-not-found | Fix the upstream cause (shell mismatch, missing tmux/asciinema, wrong artifact path) |
| Resource limits too low / OOM | Bump cpus/memory in `task.toml` within limits |
| Bad shebang / CRLF / non-executable scripts | Normalize line endings, `chmod +x` |
| Stray pipeline artifacts or wrong metadata blocking build prep | e.g. `metadata.json` in root, `cpp` vs `c++`, missing language — clean up |
| Build reproducibility | `apt-get update` before installs; bake test deps into image |

Build **may** use network; **run-time** sandbox restricts agent to model gateway; verifier airgapped.

## Not fixable environment issues

| Issue | Why |
|-------|-----|
| Tangled apt/pip/npm/cargo install failures | Adding one missing dev package or flag is worth fixing; a version-conflicted toolchain is not |
| External-network dependency at build/solve time | Vendoring one small file is fixable; a multi-GB model pull or live service is not |
| Oracle timeout after max timeout bump | If the only remaining fix reduces PR scope → Not Fixable |

For oracle timeout: raise `[agent]` (max 7200) and `[verifier]` (max 1800) timeouts first.

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
