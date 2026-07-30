# Harbor Framework — task structure

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

## task.toml schema

```toml
schema_version = "1.3"   # Harbor format version (NOT task content version)

[environment]
os                = "linux"
cpus              = 2          # 2 or 4
memory_mb         = 2048       # 2048–16384
storage_mb        = 5120       # 5120–10240
gpus              = 0          # always 0
build_timeout_sec = 600        # max 1800
network_mode      = "public"

[agent]
network_mode  = "allowlist"
allowed_hosts = ["api.portkey.ai"]
timeout_sec   = 300            # max 7200 — raise if agents timeout

[verifier]
network_mode = "no-network"
timeout_sec  = 120             # max 1800

[metadata]
category               = "..."
difficulty_explanation = "..."
source                 = "https://github.com/org/repo/pull/1234"
# base_commit_sha may appear — must match environment/repo HEAD
```

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

**fail_to_pass** must have **≥10** entries.

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
- Known edge case: try removing `curl` if agent nonzero exit persists
