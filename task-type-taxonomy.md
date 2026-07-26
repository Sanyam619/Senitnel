# Task Type Taxonomy (Category)

Each task must be labeled with a category from this taxonomy. The category describes the primary theme, topic, or activity in the task.

In addition, there exists another axis of categorization called **subtypes**, or **subcategories** (in `task.toml`). Refer to [task-creation.mdc](../.cursor/rules/task-creation.mdc) (subcategories section) for more information.

## Open categories (new submissions)

**Only these three categories accept new tasks:**

| Slug | Status |
| ---- | ------ |
| `games` | open |
| `machine-learning` | open |
| `system-administration` | open |

All other historical categories are **blocked** for new submissions. Do not start Step 2a validation or Step 2b file creation under a blocked category.

## Before creating a task (mandatory)

**Do not start Step 2a validation or Step 2b file creation until you have read this file for the chosen category.**

1. **Pick the category** using the table in [Choosing a Category](#choosing-a-category) below. If two open categories fit, choose the one that describes the **primary activity** the agent must perform. If the idea only fits a blocked category, **reject or redesign** into an open category (or drop the idea).
2. **Read that category's section** — definition, examples, and **Authoring guidance** (where present). Blocked categories must not be used for new tasks.
3. **Apply category guardrails during ideation** — reject or redesign ideas that match the category's "Reject / avoid" patterns before drafting `specs/<task-name>.md` or any file under `tasks/`.
4. **Set `task.toml` `[metadata].category`** to the exact kebab-case slug from the open set (`games`, `machine-learning`, or `system-administration`).

## Categories

### system-administration

> **Open** — accepting new submissions.

Tasks involving OS-level configuration, user management, package management, processes, or installing, configuring, and bringing up services, networks, and environments.

**Examples:**

- Configure a systemd service
- Set up user permissions
- Install and configure Nginx

**Authoring guidance:** Prefer live state reconciliation, namespace/mount/cgroup/device-node drift, restore/replay under concurrent load, destructive admin phases, and misleading status tools that only check surface health. Avoid policy-knob transcription and single-config fixes. Primary graded activity must be operating live `/etc` / `/var` (or equivalent) admin surfaces — not rewriting application source as the main solve.

### games

> **Open** — accepting new submissions.

Tasks centered on game-like or simulated environments, interactive puzzles, or simulation games that run in the terminal.

**Examples:**

- Complete a VimGolf challenge
- Solve a terminal-based puzzle
- Navigate a text adventure

**Authoring guidance:** Prefer puzzles requiring exploration and state reasoning, not scripted walkthroughs. Avoid hidden-instance "find the one broken file" difficulty. Keep tournament/contest framing (not forensics/API manuals); avoid declaring language rosters that make the surface read as software repair.

### machine-learning

> **Open** — accepting new submissions.

Tasks requiring training, fine-tuning, running inference, or evaluating machine learning models, including dependency setup, running training loops, and managing data pipelines for ML tasks.

**Examples:**

- Fine-tune a model on custom data
- Debug a training pipeline
- Optimize inference performance

**Authoring guidance:** Prefer checkpoint/resume, data-pipeline coupling, and evaluation invariants that break under subtle config drift. Avoid blank-canvas "implement this training loop from the spec" tasks.

### build-and-dependency-management

> **Currently blocked** — not accepting new submissions. Do not submit new tasks under this category until this note is removed.

Compile code, manage dependencies, build components.

**Examples:**

- Fix a broken build configuration
- Resolve dependency conflicts
- Set up a multi-stage Docker build

### data-processing

> **Currently blocked** — not accepting new submissions. Do not submit new tasks under this category until this note is removed.

Tasks that transform, parse, filter, aggregate datasets or files and directories and generate derived output.

**Examples:**

- Parse and transform CSV data
- Aggregate log files
- Filter and sort JSON datasets

### software-engineering

> **Currently blocked** — not accepting new submissions. Do not submit new tasks under this category until this note is removed.

Tasks focused on developing or testing features and algorithms, fixing bugs and improving/optimizing an existing feature, implementing tests, or maintaining software projects.

**Examples:**

- Implement a caching algorithm
- Fix a race condition
- Optimize database queries

### debugging

> **Currently blocked** — not accepting new submissions. Do not submit new tasks under this category until this note is removed.

Tasks that require identifying, diagnosing, and fixing errors in scripts, codebases, or system configurations.

**Examples:**

- Find and fix a memory leak
- Debug a failing test suite
- Diagnose a production crash

### security

> **Currently blocked** — not accepting new submissions. Do not submit new tasks under this category until this note is removed.

Tasks related to cryptography, authentication, permissions, penetration-style tests, exploit, validate vulnerabilities, reverse engineering or security configuration.

**Examples:**

- Find a SQL injection vulnerability
- Configure secure TLS settings
- Reverse engineer a binary

### scientific-computing

> **Currently blocked** — not accepting new submissions. Do not submit new tasks under this category until this note is removed.

Tasks using scientific libraries or workflows, such as numerical computation, simulations, or domain-specific research code.

**Examples:**

- Implement a numerical solver
- Debug a simulation
- Optimize a scientific computation

## Distribution Guidelines

To ensure benchmark diversity across the **open** set:

- No single open category should dominate the active submission queue
- Prefer a balanced mix of `games`, `machine-learning`, and `system-administration`

## Choosing a Category

Pick an **open** category that best describes the primary activity. If the natural fit is blocked, redesign the primary activity into an open category or reject the idea.

| Primary activity          | Category                                          |
| ------------------------- | ------------------------------------------------- |
| OS/server configuration   | `system-administration` (open)                    |
| Interactive challenges    | `games` (open)                                    |
| ML model work             | `machine-learning` (open)                         |
| Build systems, packages   | `build-and-dependency-management` (blocked)       |
| ETL, file processing      | `data-processing` (blocked)                       |
| Code development, testing | `software-engineering` (blocked)                  |
| Finding/fixing bugs       | `debugging` (blocked)                             |
| Security issues           | `security` (blocked)                              |
| Scientific code           | `scientific-computing` (blocked)                  |
