# Quality Check — agentic rubric judge

**Blocking eval.** Failing verdict → NEEDS_REVISION (same as difficulty/oracle fail).

Two LLM judges (Claude Opus + GPT-5.5) score 10 axes. Adjudicator breaks ties.

## What blocks submission

Only **test_coverage** and **test_faithfulness** drive pass/fail.

| Verdict | Condition |
|---------|-----------|
| **REMOVE** | Adjudicated score ≤2.0 on either test axis, OR essential auto-fail pattern |
| **DISCUSS** | Any judge ≤2 on test axis, OR adjudicated ≤3.0 |
| **OK** | Both test axes **>3.0**, no judge ≤2 |

**Platform pass bar:** both axes must land **above 3.0** — exactly 3.0 (or any judge at 2 or
below) → needs revision.

**EC safety margin (recommended, not platform threshold):** aim for both judges **4+** on
coverage and faithfulness — don't ship borderline.

## The two test questions

### test_coverage (Instruction → Tests)
Every instruction requirement has a real enforcing assertion. Broken solution must fail ≥1 test.

### test_faithfulness (Tests → Instruction)
Every assertion maps to something stated or reasonably implied in instruction.

## Auto-REMOVE patterns

If a judge scores ≤2 and cites one of these, task is removed outright:

| Pattern | What to look for |
|---------|------------------|
| **Silent skip** | `@pytest.mark.skip`, `skipif`, ImportError → None |
| **No CLI invocation** | Instruction requires CLI/service but tests only hit library internals |
| **Pre-created artifact passes** | `path.exists()` without content check — `touch` passes |
| **Agent controls coverage** | Tests loop over agent's own output JSON |
| **Fail-open** | `if not output.exists(): return`, broad try/except, gated assertions |
| **Overreach** | Names/formats/thresholds not in instruction and not derivable |

`validate_task.py` catches the mechanical forms of these (`@pytest.mark.skip`,
`importorskip`, `t.Skip`, `it.skip`/`xit`, `.only`, `GTEST_SKIP`, `DISABLED_`, empty
`catch {}`, `except ... pass`, exists-guard returns, unpaired existence checks). Overreach
and no-CLI-invocation still need a human read.

## Test-writing checklist

**Do:**
- Map every imperative, output field, edge case, threshold in instruction → assertion
- Test at instruction's stated strictness ("all rows" means all, not "at least one")
- Include regression test reproducing original failure
- Fixed seeds; no network/wall-clock dependence
- Fixtures baked into verifier image
- State output schema in instruction when tests assert format

**Don't:**
- Source-code substring scans (`assert "deque" in source`)
- Hidden `EXPECTED_COUNT = 47` agent can't derive
- Compare to hidden golden files not foreshadowed
- Circular checks from agent output
- Exact error strings / key order / whitespace unless instruction fixes them
- Broad try/except in test bodies

## Advisory axes (fix anyway — reviewers see them)

- **Instruction:** realism, clarity, self-containedness, prescriptiveness
- **Oracle:** spec faithfulness, no gaming, robustness/reproducibility
- **Packaging:** stray artifacts cap score at 1; solution leakage in agent paths

## Self-audit before upload

Steps 1–4 are judgment and cannot be automated — they are also what the judge scores.

1. List every requirement sentence in `instruction.md`
2. For each, name ≥1 test assertion that enforces it (coverage)
3. List every assertion in the patched tests
4. For each, cite instruction grounding or a derivable codebase name (faithfulness)

Then let the tooling cover the mechanical half. `validate_task.py` reads the added lines of
`tests.patch` — where the real tests live — and flags the auto-REMOVE patterns across
Python, Go, JS/TS and gtest, plus f2p count, id traceability, and patch integrity:

```bash
python3 scripts/validate_task.py tasks/active/<task>
./scripts/preflight.sh tasks/active/<task> --rubric   # local rubric judge
```

`--rubric` runs `harbor check`, the closest local stand-in for this blocking eval. Fix what
it cites before uploading — it costs nothing, unlike a revision.

### Enabling the rubric judge

`harbor check` calls Anthropic directly and needs a key of your own; the Portkey host in
`[agent] allowed_hosts` is for the agent inside the trial, not for this. Without the key it
exits after roughly 20 seconds, so preflight checks for it first and tells you rather than
letting you wait:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
./scripts/preflight.sh tasks/active/<task> --rubric
```

The report lands in `.preflight/<task>/rubric.json` with `rubric.log` beside it. **Not yet
run in this workspace** — the wiring is tested up to the credential check and no further, so
treat the first successful run as new information and record what the JSON actually contains.
