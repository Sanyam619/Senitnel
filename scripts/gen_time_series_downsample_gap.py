#!/usr/bin/env python3
"""Generator for tasks/time-series-downsample-gap (authoring tool, not shipped)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "time-series-downsample-gap"
REF = ROOT / ".tmp-col-ref"

INSTRUCTION = """\
Downsampled rollup queries on the events time-series namespace under `/app/data` started returning wrong aggregate counts and timestamp sums after a background compaction pass. Point lookups and range scans over the same window show missing stripe rows where keyed samples should exist, and at least one retracted bucket key still appears at the affected query window. The metrics namespace was not part of the downsample job.

Sample stripes are stored under `/app/data/columns/`; rollup sidecar indexes under `/app/data/sidecars/` use the `{namespace}.idx` naming pattern. You may edit operator tables under `/app/config/l7/` and run the documented control subcommands only. The operator reference under `/app/ops/runbooks/` documents the control tables and subcommands. Do not change Rust sources under `/app/store`.

After recovery, sorted range scans over the events namespace at the same timestamp as your point probes should return the same visible keys in lexicographic order with matching payloads. Aggregate totals at that window must match the merged stripe baseline for visible keys. Write `/output/rewind-report.json` with integer `restored_generation`, plus `events` and `metrics` objects each containing integer `visible_segments` and hex string `sidecar_digest`. The restored generation must be positive and must not exceed the ceiling generation reported by the status subcommand. Each `sidecar_digest` in the report must match the on-disk sidecar for that namespace under `/app/data/sidecars/`.
"""

TASK_TOML = """\
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "scientific-computing"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["rust", "bash"]
tags = ["time-series", "downsample", "rollup", "compaction", "wal", "secondary-index"]
expert_time_estimate_min = 90
junior_time_estimate_min = 240

[verifier]
timeout_sec = 450

[agent]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
"""

OUTPUT_CONTRACT = """\
user_visible_outputs = [
  "/output/rewind-report.json",
]

internal_harness_files = [
  "/app/data/state/runtime.json",
  "/app/data/sidecars/events.idx",
  "/app/data/sidecars/metrics.idx",
]

[structured_outputs.rewind_report]
target = "/output/rewind-report.json"
format = "json"
instruction_checks = [
  "restored_generation",
  "visible_segments",
  "sidecar_digest",
]
"""

RUNBOOK = """\
# ctl operator reference

The control binary lives at `/app/bin/ctl`. Operator tables live under `/app/config/l7/` as TOML files read at runtime.

## Operator tables

| Table file | Field | Role |
|------------|-------|------|
| `k9.toml` | `tier_c` | Roll anchor used by the roll phase |
| `m2.toml` | `seq_cutoff` | WAL replay cutoff applied during barrier |
| `p7.toml` | `phases` | Ordered recovery workflow phase list |

Decoy tables (`n3.toml`, `r8.toml`) mirror field names but are not read by `ctl`.

## Subcommands

### roll

Rolls the active journal head for one namespace using the tier anchor from operator tables.

```
/app/bin/ctl roll --ks <namespace>
```

### barrier

Applies the WAL replay cutoff from operator tables and records tombstone keys into `/app/data/state/runtime.json`.

```
/app/bin/ctl barrier
```

### rebuild

Rebuilds the rollup sidecar index for one namespace after barrier application.

```
/app/bin/ctl rebuild --ks <namespace>
```

### status

Read-only runtime snapshot (`active_gen`, `ceiling_gen`, `wal_seq`).

```
/app/bin/ctl status
```

### query

Read-only diagnostics. Supports point, range, and aggregate modes.

```
/app/bin/ctl query point --ks <namespace> --key <key> --ts <unix_ms>
/app/bin/ctl query range --ks <namespace> --lo <key> --hi <key> --ts <unix_ms>
/app/bin/ctl query aggregate --ks <namespace> --ts <unix_ms>
```

### report

Emits the recovery summary JSON.

```
/app/bin/ctl report --out /output/rewind-report.json
```

## Fixture layout

Merged namespace stripes use the `{namespace}_merged.col` filename under `/app/data/columns/`. Sidecar indexes are `/app/data/sidecars/{namespace}.idx`. Journal chains live under `/app/data/manifests/`. WAL segments are under `/app/data/wal/`. Runtime snapshots are written to `/app/data/state/runtime.json`.

## Notes

- `compact` runs forward downsample compaction against the current head and is unsafe on a partially applied recovery.
- Fast index patch helpers exist in the codebase but do not replace a full rebuild after barrier application.
"""

DOCKERFILE = """\
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build/store

COPY store/Cargo.toml store/Cargo.lock ./
COPY store/manifest/Cargo.toml manifest/
COPY store/wal/Cargo.toml wal/
COPY store/index/Cargo.toml index/
COPY store/ops/Cargo.toml ops/
COPY store/ctl/Cargo.toml ctl/

COPY store/src/ src/
COPY store/manifest/src/ manifest/src/
COPY store/wal/src/ wal/src/
COPY store/index/src/ index/src/
COPY store/ops/src/ ops/src/
COPY store/ctl/src/ ctl/src/

RUN cargo build --release --locked -p ctl

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema=2.2.0-1 \\
        tmux=3.3a-3 \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        ca-certificates=20230311+deb12u1 \\
        libutempter0 \\
        procps \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
        python-is-python3 \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=builder /build/store/target/release/ctl /app/bin/ctl
COPY config/ /app/config/
COPY data/ /app/data/
COPY store/ /app/store/
COPY ops/ /app/ops/

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

WORKDIR /root
"""


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> None:
    if not REF.is_dir():
        raise SystemExit(f"missing reference tree: {REF}")

    if TASK.exists():
        shutil.rmtree(TASK)

    shutil.copytree(REF, TASK, ignore=shutil.ignore_patterns(".DS_Store"))

    w(TASK / "instruction.md", INSTRUCTION)
    w(TASK / "task.toml", TASK_TOML)
    w(TASK / "output_contract.toml", OUTPUT_CONTRACT)
    w(TASK / "environment" / "ops" / "runbooks" / "ctl_usage.md", RUNBOOK)

    dockerfile = TASK / "environment" / "Dockerfile"
    dockerfile.write_text(DOCKERFILE)

    print(f"generated {TASK}")


if __name__ == "__main__":
    main()
