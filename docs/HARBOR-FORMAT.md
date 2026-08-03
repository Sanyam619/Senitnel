# Harbor Framework — task structure

Canonical for the task layout, `task.toml` schema, and the published resource limits. The
enforced values live in `scripts/validate_task.py`; change them there and here together, or
`scripts/check-docs.py` will fail.

## Directory layout

```
<task-id>/
├── task/                          ← you edit and zip THIS (flat contents)
│   ├── task.toml
│   ├── instruction.md
│   ├── environment/
│   │   ├── Dockerfile
│   │   ├── repo/                  # cloned base repository
│   │   └── problem_statement.md   # exact copy of instruction.md
│   ├── solution/
│   │   ├── solve.sh               # applies golden.patch
│   │   └── golden.patch           # all solution changes (rename from solution.patch if needed)
│   └── tests/
│       ├── test.sh                # runs suite, writes /logs/verifier/reward.txt
│       ├── tests.patch            # fail-to-pass tests (applied at grade time)
│       └── config.json            # execution + f2p/p2p test ids
└── runs/                          # agent logs — download only, never upload
```

## Evaluation flow

1. Agent works in `environment/repo/` inside container
2. Verifier runs `tests/test.sh` (applies `tests.patch`, runs suite)
3. Reward written to `/logs/verifier/reward.txt`
4. **1.0** = all fail-to-pass pass + no pass-to-pass regressions

## task.toml — published limits

`validate_task.py` enforces every row of this table.

| Block | Field | Allowed |
|-------|-------|---------|
| `[environment]` | `os` | e.g. `linux` |
| | `cpus` | 2 or 4 |
| | `memory_mb` | 2048–16384 |
| | `storage_mb` | 5120–10240 |
| | `gpus` | always 0 |
| | `build_timeout_sec` | max 1800 |
| | `network_mode` | `"public"` |
| `[agent]` | `network_mode` | `"allowlist"` |
| | `allowed_hosts` | `["api.portkey.ai"]` |
| | `timeout_sec` | max **7200** — set it at the ceiling; a tight limit fails tasks that would pass |
| `[verifier]` | `network_mode` | `"no-network"` |
| | `timeout_sec` | max 1800 |

Only the source, verifier, agent, and environment timeouts affect validity. Never strip the
per-block `network_mode` fields, and remove `network_mode = "none"` from
`docker_compose.yaml` if present.

## task.toml — as it actually ships

The hub's example is trimmed. Real Sentinel tasks carry more `[metadata]`, and timeouts
arrive as floats:

```toml
schema_version = "1.3"           # Harbor format version, NOT the task content version

[metadata]
category               = "implementation"
subcategory            = "feature"
coding_language        = "go"
repo_name              = "opensandbox"
repo_license           = "Apache-2.0"
source_pr_url          = "https://github.com/org/repo/pull/183"
source                 = "https://github.com/org/repo/pull/183"   # legacy alias
base_commit_sha        = "f755a673..."   # must equal environment/repo HEAD
model_difficulty       = "medium"
difficulty             = "hard"          # legacy alias
tags                   = ["egress", "nftables"]
pass_at_k_opus_4_8     = "0/3"           # measured, do not hand-edit
pass_at_k_gpt_5_5      = "0/3"
hardening_cycles       = "2"
agent_hardened         = "true"

[environment]
cpus = 4
memory_mb = 8192
storage_mb = 10240
gpus = 0
build_timeout_sec = 900.0
network_mode = "public"

[agent]
timeout_sec = 7200.0
network_mode = "allowlist"
allowed_hosts = ["api.portkey.ai"]

[verifier]
timeout_sec = 300.0
network_mode = "no-network"
```

**Do not hand-edit `pass_at_k_*`, `model_difficulty`, or `difficulty`** to satisfy a
difficulty complaint — the linter rejects tasks it reads as "easy" and the two goals pull
against each other. Flag the conflict instead (`PLATFORM-TRIAGE.md`).

## config.json shape

```json
{
  "execution": {
    "commands": ["python -m pytest -q tests/test_foo.py"],
    "timeout_sec": 1800
  },
  "grading": {
    "fail_to_pass": [
      "tests/test_foo.py::test_case_one",
      "tests/test_foo.py::test_case_two"
    ],
    "pass_to_pass": [
      "tests/test_foo.py::test_regression"
    ],
    "parser": { "framework": "pytest", "result_source": "stdout_stderr" }
  },
  "artifacts": { "reward": "/logs/verifier/reward.txt" }
}
```

**fail_to_pass** must have **11–20** entries, and every id must be traceable into
`tests.patch` — an id the runner never reports pins the reward at 0. Set
`allow_extra_failures: false` so unrelated failures cannot be ignored. (Floor and ceiling
rationale: `GUIDELINES.md` → Test requirements.)

## test.sh pattern

Harbor examples use `set -euo pipefail`. Typical flow:

```bash
git apply /tests/tests.patch
cd /workspace/repo   # or task-specific workdir
if python -m pytest -q ...; then
  echo "1.0" > /logs/verifier/reward.txt
else
  echo "0.0" > /logs/verifier/reward.txt
  exit 1
fi
```

Adapt paths to your task's Dockerfile WORKDIR.

## Regenerating tests.patch

From repo at base commit (tests NOT already in repo):

```bash
cd environment/repo
git checkout <base_commit_sha>
# add f2p test changes by hand
git add -A && git diff --cached -- <test-paths> > ../../tests/tests.patch
git checkout .   # restore repo to base
git apply --check ../../tests/tests.patch   # verify
```

## Docker build notes

- Build **may** use network; runtime sandbox is restricted
- Pin base image tag (never `:latest`)
- Install tmux, asciinema if Harbor needs them
- Bake test dependencies into image
- Known edge case: try removing `curl` from Dockerfile if agent nonzero exit persists (see `PLATFORM-TRIAGE.md`)
