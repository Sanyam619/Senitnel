#!/usr/bin/env python3
"""Validate a Sentinel Harbor task directory before upload."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_FILES = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "environment/problem_statement.md",
    "solution/solve.sh",
    "tests/test.sh",
    "tests/tests.patch",
    "tests/config.json",
]

STRAY_GLOBS = [
    "**/__pycache__",
    "**/*.pyc",
    "**/.pytest_cache",
    "**/.mypy_cache",
    "**/.ruff_cache",
    "**/.venv",
    "**/node_modules",
    "**/.DS_Store",
    "**/.idea",
    "**/.vscode",
]

TEST_AUTO_FAIL_PATTERNS = [
    (r"@pytest\.mark\.skip\b", "Silent skip: @pytest.mark.skip"),
    (r"@pytest\.mark\.skipif\b", "Silent skip: @pytest.mark.skipif"),
    (r"pytest\.importorskip\b", "Silent skip: pytest.importorskip"),
    (r"except\s+ImportError\s*:", "Silent skip: ImportError handler in tests"),
    (r"except\s+Exception\s*:\s*\n\s*pass", "Fail-open: bare except pass"),
    (r"if\s+not\s+\w+\.exists\(\)\s*:\s*\n\s*return", "Fail-open: exists guard return"),
]

MIN_F2P = 10


class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_base_commit(task_toml: str) -> str | None:
    m = re.search(r'base_commit_sha\s*=\s*"([0-9a-fA-F]+)"', task_toml)
    return m.group(1) if m else None


def check_structure(task: Path, r: Result) -> None:
    for rel in REQUIRED_FILES:
        p = task / rel
        if not p.is_file():
            r.fail(f"Missing required file: {rel}")

    repo = task / "environment" / "repo"
    if not (repo / ".git").exists():
        r.fail("Missing environment/repo/.git — real git checkout required")

    golden = task / "solution" / "golden.patch"
    legacy = task / "solution" / "solution.patch"
    if not golden.is_file() and legacy.is_file():
        r.warn("Found solution/solution.patch — rename to solution/golden.patch")
    elif not golden.is_file() and not legacy.is_file():
        r.fail("Missing solution/golden.patch")


def check_instruction_sync(task: Path, r: Result) -> None:
    inst = task / "instruction.md"
    prob = task / "environment" / "problem_statement.md"
    if inst.is_file() and prob.is_file():
        if read_text(inst) != read_text(prob):
            r.fail("instruction.md and environment/problem_statement.md differ — run sync-problem-statement.sh")


def check_task_toml(task: Path, r: Result) -> None:
    path = task / "task.toml"
    if not path.is_file():
        return
    text = read_text(path)

    if "schema_version" not in text:
        r.warn("task.toml missing schema_version (expected Harbor 1.3)")

    if 'network_mode      = "public"' not in text and 'network_mode = "public"' not in text:
        r.fail("[environment] network_mode should be \"public\"")

    if "allowlist" not in text:
        r.fail("[agent] network_mode should be \"allowlist\"")
    if "api.portkey.ai" not in text:
        r.warn("[agent] allowed_hosts should include api.portkey.ai")

    if 'network_mode = "no-network"' not in text:
        r.fail("[verifier] network_mode should be \"no-network\"")

    if re.search(r"gpus\s*=\s*[1-9]", text):
        r.fail("gpus must be 0")

    if "allow_internet" in text:
        r.warn("TERMINUS-style allow_internet found — Sentinel uses per-block network_mode")

    compose = task / "environment" / "docker-compose.yaml"
    if compose.is_file() and "network_mode" in read_text(compose) and "none" in read_text(compose):
        r.fail("Remove network_mode = \"none\" from environment/docker-compose.yaml")


def check_config_json(task: Path, r: Result, strict: bool) -> None:
    path = task / "tests" / "config.json"
    if not path.is_file():
        return
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as e:
        r.fail(f"tests/config.json invalid JSON: {e}")
        return

    grading = data.get("grading", {})
    f2p = grading.get("fail_to_pass", [])
    p2p = grading.get("pass_to_pass", [])

    if not f2p:
        r.fail("tests/config.json: fail_to_pass is empty")
    elif len(f2p) < MIN_F2P:
        r.fail(f"tests/config.json: only {len(f2p)} fail_to_pass tests (need ≥{MIN_F2P})")
    elif len(f2p) < 15 and strict:
        r.warn(f"Only {len(f2p)} fail_to_pass — aim for 10–20")

    if not p2p:
        r.warn("tests/config.json: pass_to_pass empty — regression guard recommended")

    reward = data.get("artifacts", {}).get("reward", "")
    if reward and reward != "/logs/verifier/reward.txt":
        r.warn(f"Unusual reward path: {reward}")


def check_stray_artifacts(task: Path, r: Result) -> None:
    for pattern in STRAY_GLOBS:
        for hit in task.glob(pattern):
            if hit.is_dir() or hit.is_file():
                r.fail(f"Stray artifact (packaging axis fail): {hit.relative_to(task)}")


def check_test_patterns(task: Path, r: Result) -> None:
    tests_dir = task / "tests"
    for path in tests_dir.rglob("*"):
        if path.suffix not in {".py", ".sh"}:
            continue
        if path.name == "tests.patch":
            continue
        text = read_text(path)
        for pattern, msg in TEST_AUTO_FAIL_PATTERNS:
            if re.search(pattern, text, re.MULTILINE):
                r.warn(f"{path.relative_to(task)}: possible Quality Check auto-fail — {msg}")


def check_leakage_hints(task: Path, r: Result) -> None:
    inst = task / "instruction.md"
    if not inst.is_file():
        return
    text = read_text(inst).lower()
    if re.search(r"github\.com/.+/pull/\d+", text):
        r.fail("instruction.md contains PR URL (leakage)")
    if "where to look:" in text:
        r.fail("instruction.md contains 'Where to look:' (over-prescriptive)")
    if re.search(r"\bthe tests reference\b", text):
        r.fail("instruction.md exposes verifier internals")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", type=Path, help="Path to unzipped task/ contents")
    parser.add_argument("--strict", action="store_true", help="Extra warnings for borderline issues")
    args = parser.parse_args()

    task = args.task_dir.resolve()
    if not task.is_dir():
        print(f"ERROR: not a directory: {task}", file=sys.stderr)
        return 2

    r = Result()
    check_structure(task, r)
    check_instruction_sync(task, r)
    check_task_toml(task, r)
    check_config_json(task, r, args.strict)
    check_stray_artifacts(task, r)
    check_test_patterns(task, r)
    check_leakage_hints(task, r)

    for w in r.warnings:
        print(f"WARN  {w}")
    for e in r.errors:
        print(f"FAIL  {e}")

    if r.ok:
        print(f"PASS  {task}")
        if r.warnings:
            print(f"      ({len(r.warnings)} warning(s))")
        return 0
    print(f"\n{len(r.errors)} error(s), {len(r.warnings)} warning(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
