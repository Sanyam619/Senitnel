# When to skip a task

Use **Skip** on Snorkel when finishing the task is a bad use of EC time — not when you are
lazy or stuck on the first hard bug. Skipping returns the task to the pool for someone else.

**Agent obligation:** During Step 1 (or eval triage), if skip criteria match, recommend skip
with a copy-paste reason from this doc. Do not keep revising a task that should be skipped.

---

## Skip vs other verdicts

| Outcome | When |
|---------|------|
| **Valid-as-is** | No edits needed; upload as-is |
| **Fixable** | You can fix instruction/tests/oracle/env and pass evals |
| **Invalid / Not Fixable** | PR scope reduction, broken env EC cannot fix — submit Invalid form |
| **Skip** | Task is valid in theory but **you should not continue** — wrong fit, unrecoverable difficulty, or cannot reach platform bar without breaking rules |

Skip is **not** a substitute for Invalid. Use Invalid when you can document why the task is
broken. Use Skip when **you** should release the task.

---

## When to skip (checklist)

Skip if **any** of these is true after honest review + platform evals:

### 1. Difficulty cannot reach MEDIUM+ (most common after EC work)

- Agent Runner: `FAIL EASY — Requires at least MEDIUM`
- Reference agents pass **~100%** (e.g. 8/8 Opus + 8/8 GPT) while metadata says `hard`
- QC and oracle already pass — only difficulty fails
- Raising difficulty would require either:
  - **Scope expansion** so large it is risky / unrealistic for EC turnaround, or
  - **Instruction de-clarity** that would break QC faithfulness you already fixed

**Platform radio:** **Other**

### 2. Not Fixable but skip is faster than Invalid paperwork

- Clear PR scope reduction or unfixable env
- You have no bandwidth for Invalid form + reviewer back-and-forth
- Prefer: **Invalid** when you can document; **Skip** only if platform policy allows and task is clearly broken

**Platform radio:** **The input data is invalid or cannot be expanded on** OR **Other**

### 3. Outside specialty / cannot judge fairly

- Domain requires expertise you do not have (e.g. niche crypto, medical device regs)
- You cannot verify oracle correctness in reasonable time

**Platform radio:** **The question is outside my specialty area**

### 4. Genuinely ambiguous platform task (rare)

- Source PR, instruction, and tests contradict with no Fixable path
- Not Fixable and not worth Invalid submission

**Platform radio:** **The question is unclear or ambiguous**

### 5. Time sink with low acceptance probability

- Multiple revision cycles; each fix creates a new eval failure
- Marginal acceptance vs starting a fresh task

**Platform radio:** **The question is too time-consuming to answer** OR **Other** (prefer **Other** with specifics)

---

## When NOT to skip

- First Fixable issue (instruction typo, network_mode, f2p count) — **fix it**
- Oracle flake (infra) — **fix Dockerfile/config**, do not skip
- QC coverage/faithfulness — **fix tests/instruction**, do not skip
- Agent Runner `Solvable: False` with **require_solvable disabled** and agents pass — **not a skip by itself**
- You have not read `runs/` or eval logs — **investigate first**

---

## Platform skip form

Snorkel shows five radios + optional text:

| Radio | Use when |
|-------|----------|
| Outside my specialty area | Domain you cannot evaluate |
| Unclear or ambiguous | Task contradicts itself; no Fixable path |
| Too time-consuming | Only if true time sink; prefer **Other** with metrics |
| Invalid or cannot be expanded on | Not Fixable (scope/env); or cannot expand to required difficulty |
| **Other (please specify)** | **Default for difficulty FAIL EASY, multi-cycle stalls, nuanced cases** |

Always fill **Other** text when selecting **Other**. Be specific: eval name, numbers, what passed, what failed, why you stop.

---

## Copy-paste templates

### Difficulty FAIL EASY (100% agent pass, QC/oracle OK)

**Radio:** Other

```
Agent Runner failed difficulty: FAIL EASY — requires at least MEDIUM. Post-EC evals show
100% agent pass (e.g. 8/8 Opus, 8/8 GPT-5.5). Oracle 3/3, nop 0/1, Quality Check OK.
Task was agent_hardened at 0/3 originally; instruction and Dockerfile fixes needed for QC/oracle
made the task too easy to recover MEDIUM+ without large scope expansion that conflicts with
PR bounds and test faithfulness. Skipping so another EC or author can re-hard or re-scope.
```

### Not Fixable — scope (prefer Invalid if submitting form)

**Radio:** The input data is invalid or cannot be expanded on

```
Fixing requires reducing or replacing source PR scope (not allowed). Example: [one sentence
on what the PR implements vs what instruction/tests require]. Cannot expand into a valid
Sentinel task within EC guidelines. Skipping.
```

### Not Fixable — environment

**Radio:** The input data is invalid or cannot be expanded on

```
Environment cannot be repaired with allowed EC Dockerfile fixes: [build failure / external
network at solve time / oracle timeout after timeout bump]. Skipping.
```

### Outside specialty

**Radio:** The question is outside my specialty area

```
Task requires deep expertise in [domain] to verify oracle and instruction faithfully.
I cannot confidently validate correctness or difficulty in reasonable time. Skipping.
```

### Revision spiral

**Radio:** Other

```
After [N] revision cycles, evals pass [QC/oracle/static] but fail [difficulty/other].
Each fix causes [specific regression]. Low probability of Accept vs EC time. Skipping.
```

---

## Agent workflow

1. Step 1 or Step 5: check skip criteria above.
2. If skip recommended, tell user:
   - **Skip recommended** + which criterion
   - Platform radio to pick
   - Copy-paste **Other** text (customize with task name + eval numbers)
3. Do **not** zip or continue Step 2–4 unless user says to try anyway.
4. Log skip in `docs/EC-LEARNINGS.md` session log with eval evidence.

---

## Example: casbin-node-casbin PR378 (2026-08-01)

| Eval | Result |
|------|--------|
| Quality Check | OK |
| Oracle | 3/3 |
| Agent pass | 100% Opus 8/8, 100% GPT 8/8 |
| Difficulty | **FAIL EASY — requires at least MEDIUM** |

**Decision:** Skip (criterion 1). **Radio:** Other. Use template above.
