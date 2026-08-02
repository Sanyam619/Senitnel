# Reviewer guide (condensed)

For ECs reviewing another submitter's Sentinel Ultra submission. Full detail in
`docs/hub-scrape/tasking.txt` (reviewer section).

## Your role

Independently verify the submitter's findings using the same document review as the submitter.
You are **not required** to run Harbor, oracle, or NOP locally — but you may if it helps.

Give your **own** verdict regardless of whether it matches the submitter's.

## Outcomes

| Outcome | When |
|---------|------|
| **Accept** | Accurate, complete, well-supported submission |
| **Needs Revision** | Task still has fixable authoring errors |
| **Reject** | **Only** when max revision cycles exhausted and "Needs Revision" is blocked |

Reject is **not** a substitute for Needs Revision while the submitter can still revise.

When platform shows **Maximum Revisions Reached**: click I Understand → select Reject (or Accept
with notes if Reject unavailable).

## By submitter verdict

### Valid as-is
- Repeat submitter workflow (instruction, PR cross-check, environment skim, solution/tests read)
- Sanity-check coherence instruction ↔ tests ↔ oracle ↔ PR
- Verify `task.toml` metadata (source, timeouts, network blocks)
- Confirm no PR scope deviation

### Not Fixable / Invalid
- Confirm each reported issue holds on inspection
- Agree reason matches Not Fixable categories in `docs/GUIDELINES.md`
- Check submitter notes match what you see

### Fixable
- Inspect rewrites resolve reported issues without new misalignment or leakage
- Confirm PR expansion only **adds** to original scope (never reduces/replaces)
- Verify upload is full corrected bundle
- Review `runs/` if submitter cited agent behavior

## Needs Revision — error categories (internal tags)

Instruction Styling · Instruction Prescriptiveness · Test ↔ Instruction Misalignment ·
Test Coverage Issues · Exposing Hints/Answers · Oracle Solution Issues · PR Scope Violation ·
Test Build Issues · Time-Based Tests · Task Difficulty · Metadata Issues · Uses Internet ·
Agent Timeout · Wrong Coding Language · Test Dependency Location · Pinning Issues ·
Environment · PR Relevancy · Other

## Submission Quality Score (1–5)

| Score | Meaning | Action |
|-------|---------|--------|
| 1 | Wrong source / spam / low effort | Needs Revision |
| 2 | Gaps — untested reqs, misalignment, bundle issues | Needs Revision |
| 3 | Correct; minor issues only | Accept |
| 4 | Thorough, no significant issues | Accept |
| 5 | Reference quality | Accept |

## Rebuttal ack (required)

Before submit, read submitter's **Comments for Reviewer** and confirm:
- Rebuttal does not change outcome, OR
- Rebuttal changed outcome, OR
- No rebuttal available
