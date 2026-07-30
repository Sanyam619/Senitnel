# Quality Check — agentic rubric judge

**Blocking eval.** Failing verdict → NEEDS_REVISION (same as difficulty/oracle fail).

Two LLM judges (Claude Opus + GPT-5.5) score 10 axes. Adjudicator breaks ties.

## What blocks submission

Only **test_coverage** and **test_faithfulness** drive pass/fail.

| Verdict | Condition |
|---------|-----------|
| **REMOVE** | Adjudicated score ≤2.0 on either test axis, OR essential auto-fail pattern |
| **DISCUSS** | Any judge ≤2 on test axis, OR adjudicated ≤3.0 |
| **OK** | Both test axes >3.0, no judge ≤2 |

**Practical bar:** both judges rate tests **4+** on coverage and faithfulness.

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

1. List every requirement sentence in `instruction.md`
2. For each, find ≥1 test assertion (coverage)
3. List every assertion in patched tests
4. For each, find instruction grounding or derivable codebase name (faithfulness)
5. Count f2p entries in `config.json` — need ≥10
6. Grep tests for `skip`, `pytest.importorskip`, bare `exists()`, `try:...except: pass`

```bash
python3 scripts/validate_task.py tasks/active/<task> --strict
```
