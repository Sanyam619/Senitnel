#!/usr/bin/env python3
"""Validate a Sentinel Harbor task directory before upload.

Mirrors the platform's blocking gates as closely as a local script can:
structure, task.toml limits, the fail-to-pass contract, the Quality Check
auto-REMOVE patterns (read out of tests.patch, where the real tests live),
tests.patch integrity, packaging hygiene, and instruction leakage.

Exit codes: 0 = pass (warnings allowed), 1 = at least one failure, 2 = bad usage.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
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

# Lower bound: the platform's Fixable/Valid-as-is confirmation checkbox reads
# "More than 10 fail-to-pass tests", so exactly 10 makes that box false.
# Upper bound: not in the hub guidelines — observed CodeBuild `run_static_checks`
# rejection at 21 f2p (see docs/EC-LEARNINGS.md, dc0540bb). The hub's own
# "ideally 10-20" makes 20 a safe ceiling either way.
MIN_F2P = 11
MAX_F2P = 20

# Published limits from the Harbor task-metadata reference.
LIMITS = {
    "environment": {
        "cpus": ("in", (2, 4)),
        "memory_mb": ("range", (2048, 16384)),
        "storage_mb": ("range", (5120, 10240)),
        "build_timeout_sec": ("max", 1800),
    },
    "agent": {"timeout_sec": ("max", 7200)},
    "verifier": {"timeout_sec": ("max", 1800)},
}

NETWORK_MODES = {
    "environment": "public",
    "agent": "allowlist",
    "verifier": "no-network",
}

STRAY_NAMES = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv",
    "node_modules", ".DS_Store", ".idea", ".vscode", "__MACOSX",
}
STRAY_SUFFIXES = (".pyc", ".swp", ".orig", ".bak", "~")

TEST_PATH_HINT = re.compile(
    r"(^|/)(tests?|spec|__tests__|testdata)(/|$)"
    r"|(^|/)test_[^/]+\.py$"
    r"|_test\.(go|py|cc|cpp|rb)$"
    r"|\.(test|spec)\.(ts|tsx|js|jsx|mjs)$"
    r"|(^|/)[^/]*_test\.[a-z]+$"
    r"|Test[^/]*\.(java|kt|cs)$",
    re.IGNORECASE,
)

# Quality Check auto-REMOVE patterns, per language. Matched against *added*
# lines in tests.patch only — that is the code the judge reads.
AUTO_FAIL = [
    (r"@pytest\.mark\.skip\b", "silent skip (@pytest.mark.skip)"),
    (r"@pytest\.mark\.skipif\b", "silent skip (@pytest.mark.skipif)"),
    (r"pytest\.importorskip\b", "silent skip (pytest.importorskip)"),
    (r"pytest\.skip\s*\(", "silent skip (pytest.skip)"),
    (r"unittest\.skip", "silent skip (unittest.skip)"),
    (r"except\s+ImportError", "silent skip (ImportError swallowed)"),
    (r"except[^\n]*:\s*pass\b", "fail-open (except ... pass)"),
    (r"except[^\n]*:\s*\n\s*pass\b", "fail-open (except ... pass)"),
    (r"\bt\.Skip(f|Now)?\s*\(", "silent skip (Go t.Skip)"),
    (r"testing\.Short\s*\(\s*\)", "conditional skip (Go testing.Short)"),
    (r"\b(it|test|describe|context)\.skip\s*\(", "silent skip (JS .skip)"),
    (r"\b(xit|xdescribe|xtest)\s*\(", "silent skip (JS xit/xdescribe)"),
    (r"\b(it|test|describe)\.only\s*\(", "coverage shrink (JS .only skips siblings)"),
    (r"GTEST_SKIP\s*\(", "silent skip (GTEST_SKIP)"),
    (r"\b(TEST|TEST_F|TEST_P)\s*\(\s*\w*,\s*DISABLED_", "silent skip (gtest DISABLED_)"),
    (r"catch\s*\([^)]*\)\s*\{\s*\}", "fail-open (empty catch block)"),
    (r"if\s+not\s+[\w.]+\.exists\(\)\s*:\s*(return|pass)", "fail-open (exists guard returns)"),
    (r"\bcontinue\s*#\s*(skip|ignore)", "fail-open (silently continues)"),
]

# Assertions that read source text instead of behavior.
SOURCE_SCAN = [
    (r"(read_text|readFileSync|read\(\))[^\n]*\b(assert|expect|require)", "asserts on file contents read as text"),
    (r"assert\s+[\"'][^\"']+[\"']\s+in\s+(src|source|code|content|text)\b", "asserts substring of source code"),
    (r"\bgrep\b", "shells out to grep instead of running code"),
]


class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# tests.patch parsing
#
# File classification (create / delete / rename / mode change / binary) and the
# authoritative per-file line counts come from `git apply`, which owns this file
# format. Parsed locally: only the *content* of added lines, which the pattern
# scans need, plus a raw count of `+` lines.
#
# That raw count is not redundant. `git apply --numstat` reports the number of
# lines git will actually add, and `--check` passes, even when an @@ header
# undercounts its hunk — git silently drops the surplus lines, truncating the
# file on apply. Comparing git's count against the `+` lines present in the text
# is what catches that (observed twice locally, see docs/EC-LEARNINGS.md).
# --------------------------------------------------------------------------- #
class PatchFile:
    def __init__(self, path: str) -> None:
        self.path = path
        self.is_new = False
        self.is_delete = False
        self.is_binary = False
        self.added: list[str] = []
        self.plus_lines = 0  # `+` lines present in the patch text
        self.minus_lines = 0
        self.git_add: int | None = None  # lines git will actually add
        self.git_del: int | None = None


def _unquote(path: str) -> str:
    path = path.strip()
    if path.startswith('"') and path.endswith('"'):
        try:
            return path[1:-1].encode().decode("unicode_escape")
        except UnicodeDecodeError:
            return path[1:-1]
    return path


def _strip_prefix(path: str) -> str:
    path = _unquote(path)
    return re.sub(r"^[ab]/", "", path)


def scan_patch_text(text: str) -> list[PatchFile]:
    """Collect added-line content per file. Structure comes from git, not here."""
    files: list[PatchFile] = []
    cur: PatchFile | None = None
    in_hunk = False

    for line in text.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git (.+) (.+)$", line)
            path = _strip_prefix(m.group(2)) if m else line.split()[-1]
            cur = PatchFile(path)
            files.append(cur)
            in_hunk = False
            continue
        if cur is None:
            continue
        if line.startswith("GIT binary patch"):
            cur.is_binary = True
            in_hunk = False
            continue
        if line.startswith("--- "):
            if line[4:].strip() == "/dev/null":
                cur.is_new = True
            in_hunk = False
            continue
        if line.startswith("+++ "):
            target = line[4:].strip()
            if target == "/dev/null":
                cur.is_delete = True
            else:
                cur.path = _strip_prefix(target)
            in_hunk = False
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+"):
            cur.plus_lines += 1
            cur.added.append(line[1:])
        elif line.startswith("-"):
            cur.minus_lines += 1
    return files


class GitPatchFacts:
    """What `git apply` says about a patch."""

    def __init__(self) -> None:
        self.available = False
        self.error: str | None = None
        self.numstat: list[tuple[int | None, int | None, str]] = []
        self.created: set[str] = set()
        self.deleted: set[str] = set()
        self.renames: list[str] = []
        self.mode_changes: list[str] = []


def git_patch_facts(patch: Path) -> GitPatchFacts:
    facts = GitPatchFacts()
    if shutil.which("git") is None:
        facts.error = "git not on PATH"
        return facts

    # `git apply` drops patched paths that sit outside the current directory when
    # it is run inside a work tree, which would silently report an empty diff.
    # Run it from a scratch directory with repository discovery disabled.
    with tempfile.TemporaryDirectory() as scratch:
        env = {**os.environ, "GIT_CEILING_DIRECTORIES": scratch}

        def run(*flags: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", "apply", *flags, "--", str(patch.resolve())],
                cwd=scratch, env=env, capture_output=True, text=True, check=False,
            )

        numstat = run("--numstat", "-z")
        if numstat.returncode != 0:
            facts.error = (numstat.stderr or numstat.stdout).strip() or "git apply --numstat failed"
            return facts
        summary = run("--summary")

    facts.available = True
    for record in numstat.stdout.split("\0"):
        if not record.strip():
            continue
        parts = record.split("\t", 2)
        if len(parts) != 3:
            continue
        add, dele, path = parts
        facts.numstat.append((
            None if add == "-" else int(add),
            None if dele == "-" else int(dele),
            _unquote(path),
        ))

    for line in summary.stdout.splitlines():
        line = line.strip()
        if line.startswith("create mode "):
            facts.created.add(_unquote(line.split(maxsplit=3)[-1]))
        elif line.startswith("delete mode "):
            facts.deleted.add(_unquote(line.split(maxsplit=3)[-1]))
        elif line.startswith("rename "):
            facts.renames.append(line)
        elif line.startswith("mode change "):
            facts.mode_changes.append(line)
    return facts


def load_patch(patch: Path) -> tuple[list[PatchFile], GitPatchFacts]:
    """Merge git's structural facts with locally scanned added-line content."""
    files = scan_patch_text(read_text(patch))
    facts = git_patch_facts(patch)
    if not facts.available:
        return files, facts

    by_path = {f.path: f for f in files}
    merged: list[PatchFile] = []
    for add, dele, path in facts.numstat:
        pf = by_path.get(path)
        if pf is None:
            # Rename or an unusual header shape: fall back to basename matching so
            # the file still gets its counts rather than dropping out of the list.
            tail = Path(path).name
            pf = next((f for f in files if Path(f.path).name == tail), None) or PatchFile(path)
        pf.path = path
        pf.git_add, pf.git_del = add, dele
        pf.is_binary = pf.is_binary or add is None
        pf.is_new = path in facts.created
        pf.is_delete = path in facts.deleted
        merged.append(pf)
    return merged, facts


def check_patch_applies(task: Path, r: Result) -> None:
    """Both patches must apply to the shipped base repo, or every trial errors."""
    repo = task / "environment" / "repo"
    if not (repo / ".git").exists() or shutil.which("git") is None:
        return
    for rel in ("tests/tests.patch", "solution/golden.patch"):
        patch = task / rel
        if not patch.is_file():
            continue
        proc = subprocess.run(
            ["git", "apply", "--check", "--", str(patch.resolve())],
            cwd=repo, capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            r.fail(
                f"{rel} does not apply to environment/repo at base — every trial will error. "
                f"git says: {detail[0] if detail else 'unknown error'} "
                "(check the repo is clean and at base_commit_sha)"
            )


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def check_structure(task: Path, r: Result) -> None:
    for rel in REQUIRED_FILES:
        if not (task / rel).is_file():
            r.fail(f"missing required file: {rel}")

    if not (task / "environment" / "repo" / ".git").exists():
        r.fail("missing environment/repo/.git — the shipped repo must be a real checkout")

    golden = task / "solution" / "golden.patch"
    legacy = task / "solution" / "solution.patch"
    if not golden.is_file():
        if legacy.is_file():
            r.fail("solution/solution.patch found — rename it to solution/golden.patch")
        else:
            r.fail("missing solution/golden.patch")
    else:
        lines = len(read_text(golden).splitlines())
        touched = len(re.findall(r"^diff --git ", read_text(golden), re.MULTILINE))
        r.note(f"golden.patch: {lines} lines across {touched} file(s)")
        if lines < 100 or touched < 2:
            r.warn(
                f"golden.patch is {lines} lines across {touched} file(s) — the authenticity "
                "bar is roughly 100+ lines across 2+ files"
            )

    if (task / "runs").exists():
        r.fail("runs/ is inside the task directory — it must never ship in the upload zip")

    solve = task / "solution" / "solve.sh"
    if solve.is_file() and "golden.patch" not in read_text(solve):
        r.warn("solution/solve.sh does not mention golden.patch — confirm it applies the oracle")


def check_instruction_sync(task: Path, r: Result) -> None:
    inst = task / "instruction.md"
    prob = task / "environment" / "problem_statement.md"
    if inst.is_file() and prob.is_file() and read_text(inst) != read_text(prob):
        r.fail(
            "instruction.md != environment/problem_statement.md — "
            "run ./scripts/sync-problem-statement.sh"
        )


def _limit_check(block: str, key: str, value, rule, r: Result) -> None:
    kind, bound = rule
    if not isinstance(value, (int, float)):
        r.warn(f"[{block}] {key} is not numeric: {value!r}")
        return
    if kind == "in" and value not in bound:
        r.fail(f"[{block}] {key} = {value} — allowed values are {bound[0]} or {bound[1]}")
    elif kind == "range" and not (bound[0] <= value <= bound[1]):
        r.fail(f"[{block}] {key} = {value} — must be between {bound[0]} and {bound[1]}")
    elif kind == "max" and value > bound:
        r.fail(f"[{block}] {key} = {value} — maximum is {bound}")


def check_task_toml(task: Path, r: Result) -> None:
    path = task / "task.toml"
    if not path.is_file():
        return
    raw = read_text(path)
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        r.fail(f"task.toml is not valid TOML: {exc}")
        return

    if "schema_version" not in data:
        r.warn("task.toml has no schema_version (expected Harbor \"1.3\")")

    for block, expected in NETWORK_MODES.items():
        section = data.get(block)
        if not isinstance(section, dict):
            r.fail(f"task.toml is missing the [{block}] block")
            continue
        actual = section.get("network_mode")
        if actual is None:
            r.fail(f'[{block}] network_mode is missing — must be "{expected}"')
        elif actual != expected:
            r.fail(f'[{block}] network_mode = "{actual}" — must be "{expected}"')
        for key, rule in LIMITS.get(block, {}).items():
            if key in section:
                _limit_check(block, key, section[key], rule, r)

    env = data.get("environment", {})
    if isinstance(env, dict):
        if env.get("gpus", 0) != 0:
            r.fail(f"[environment] gpus = {env.get('gpus')} — must be 0")
        for key in ("cpus", "memory_mb", "storage_mb", "build_timeout_sec"):
            if key not in env:
                r.warn(f"[environment] {key} not set — platform defaults may fall outside limits")

    agent = data.get("agent", {})
    if isinstance(agent, dict):
        hosts = agent.get("allowed_hosts") or []
        if "api.portkey.ai" not in hosts:
            r.fail('[agent] allowed_hosts must include "api.portkey.ai"')
        timeout = agent.get("timeout_sec")
        if isinstance(timeout, (int, float)) and timeout < 7200:
            r.warn(
                f"[agent] timeout_sec = {int(timeout)} — the ceiling was raised to 7200 "
                "(hub changelog Jul 23) and a tight ceiling fails tasks that would pass"
            )

    meta = data.get("metadata", {})
    if isinstance(meta, dict):
        source = meta.get("source") or meta.get("source_pr_url")
        if not source:
            r.fail("[metadata] needs a source URL (source / source_pr_url)")
        elif not str(source).startswith("http"):
            r.warn(f"[metadata] source does not look like a URL: {source}")
        if not meta.get("category"):
            r.warn("[metadata] category is empty — the packaging axis cross-checks metadata")
        if not (meta.get("difficulty_explanation") or meta.get("model_difficulty") or meta.get("difficulty")):
            r.warn("[metadata] no difficulty_explanation / model_difficulty")

    if not re.search(r'base_commit_sha\s*=\s*"[0-9a-fA-F]{7,40}"', raw):
        r.warn("no base_commit_sha in task.toml — git hygiene cannot verify HEAD alignment")

    if "allow_internet" in raw:
        r.warn("allow_internet is a Terminus field — Sentinel uses per-block network_mode")

    for name in ("docker-compose.yaml", "docker_compose.yaml", "docker-compose.yml"):
        for compose in (task / name, task / "environment" / name):
            if compose.is_file() and re.search(r'network_mode\s*=?:?\s*"?none"?', read_text(compose)):
                r.fail(f'remove network_mode = "none" from {compose.relative_to(task)}')


def _id_in_patch(test_id: str, blob: str) -> bool:
    """Best-effort match of a config.json test id against added patch lines.

    Ids differ per runner: `path/to/file.py::test_name`, `Suite.TestName`,
    `pkg::TestName`, or a plain vitest/jest title with spaces. Try the whole id,
    then its trailing segments, then fall back to requiring every identifier-like
    word to appear somewhere in the patch.
    """
    test_id = re.sub(r"\[.*\]$", "", test_id.strip())  # drop pytest parametrisation
    if not test_id:
        return True
    candidates = {test_id}
    for sep in ("::", "/", "."):
        if sep in test_id:
            candidates.add(test_id.rsplit(sep, 1)[-1])
    if any(c and c in blob for c in candidates):
        return True
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", test_id)
    return bool(words) and all(w in blob for w in words)


def check_config_json(task: Path, r: Result, patch_files: list[PatchFile]) -> None:
    path = task / "tests" / "config.json"
    if not path.is_file():
        return
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        r.fail(f"tests/config.json is not valid JSON: {exc}")
        return

    grading = data.get("grading", {}) or {}
    f2p = grading.get("fail_to_pass") or []
    p2p = grading.get("pass_to_pass") or []
    r.note(f"fail_to_pass: {len(f2p)}   pass_to_pass: {len(p2p)}")

    if not f2p:
        r.fail("tests/config.json: fail_to_pass is empty")
    elif len(f2p) < MIN_F2P:
        r.fail(
            f"tests/config.json: {len(f2p)} fail_to_pass tests — need {MIN_F2P}-{MAX_F2P} "
            '(the platform confirmation reads "More than 10")'
        )
    elif len(f2p) > MAX_F2P:
        r.fail(f"tests/config.json: {len(f2p)} fail_to_pass tests — keep it at or below {MAX_F2P}")

    if len(set(f2p)) != len(f2p):
        r.fail("tests/config.json: fail_to_pass contains duplicate ids")
    overlap = set(f2p) & set(p2p)
    if overlap:
        r.fail(f"tests/config.json: ids in both fail_to_pass and pass_to_pass: {sorted(overlap)[:3]}")

    if not p2p:
        r.warn("tests/config.json: pass_to_pass is empty — no regression guard on existing behavior")

    if grading.get("allow_extra_failures", True):
        r.warn(
            "tests/config.json: allow_extra_failures is true — unrelated test failures will not "
            "affect the reward; set false so the suite grades the whole run"
        )

    parser = grading.get("parser") or {}
    if not parser.get("framework"):
        r.warn("tests/config.json: grading.parser.framework is unset")

    execution = data.get("execution") or {}
    if not execution.get("commands"):
        r.warn("tests/config.json: execution.commands is empty — relying on framework defaults")

    reward = (data.get("artifacts") or {}).get("reward", "")
    if reward and reward != "/logs/verifier/reward.txt":
        r.warn(f"tests/config.json: unusual reward path {reward}")

    # Every declared f2p id should be traceable into the patch that injects the
    # tests. An id that matches nothing can never pass, so the reward is pinned
    # at 0 no matter what the agent does.
    if patch_files and f2p:
        blob = "\n".join("\n".join(f.added) for f in patch_files)
        missing = [tid for tid in f2p if not _id_in_patch(tid, blob)]
        if len(missing) == len(f2p):
            r.fail(
                "no fail_to_pass id in tests/config.json can be found in tests/tests.patch — "
                f"the ids will never match ({f2p[0]!r})"
            )
        elif missing:
            r.warn(
                f"{len(missing)} fail_to_pass id(s) not obviously present in tests.patch — "
                f"confirm the ids match what the runner reports: {missing[:3]}"
            )


def check_tests_patch(
    task: Path, r: Result, patch_files: list[PatchFile], facts: GitPatchFacts
) -> None:
    patch = task / "tests" / "tests.patch"
    if not patch.is_file():
        return
    if not facts.available:
        if facts.error and "not on PATH" not in facts.error:
            r.fail(f"tests/tests.patch is malformed — git apply rejects it: {facts.error}")
            return
        r.warn("git unavailable — tests.patch line counts and structure were not verified")
    if not patch_files:
        r.fail("tests/tests.patch has no parseable diff headers")
        return

    for pf in patch_files:
        if pf.git_add is None or pf.is_binary:
            continue
        if pf.git_add != pf.plus_lines:
            r.fail(
                f"tests.patch corrupt hunk header in {pf.path}: the patch text has "
                f"{pf.plus_lines} added line(s) but git will add {pf.git_add} — the @@ counts "
                "are wrong and the file applies truncated (git does not complain)"
            )
        if pf.git_del != pf.minus_lines:
            r.fail(
                f"tests.patch corrupt hunk header in {pf.path}: the patch text removes "
                f"{pf.minus_lines} line(s) but git will remove {pf.git_del}"
            )

    for line in facts.renames:
        r.fail(f"tests.patch renames a file ({line}) — tests must be added, not moved")
    for line in facts.mode_changes:
        r.warn(f"tests.patch changes a file mode ({line}) — confirm that is intentional")
    for pf in patch_files:
        if pf.is_binary:
            r.warn(f"tests.patch ships a binary blob ({pf.path}) — prefer generating fixtures in code")

    new_tests = [p for p in patch_files if p.is_new]
    modified = [p for p in patch_files if not p.is_new and not p.is_delete]
    r.note(f"tests.patch: {len(new_tests)} new file(s), {len(modified)} modified")

    for pf in patch_files:
        if pf.is_delete:
            r.fail(f"tests.patch deletes {pf.path} — never remove existing tests")

    for pf in modified:
        if TEST_PATH_HINT.search(pf.path):
            r.warn(
                f"tests.patch modifies the pre-existing test file {pf.path} — the harness "
                "requires pre-existing test files to stay byte-identical to base, and agents "
                "editing the same file make the patch fail. Add a new eval_* file instead"
            )
        else:
            r.warn(
                f"tests.patch modifies the non-test file {pf.path} — if that file changed "
                "upstream the patch will not apply; confirm it is required for the build"
            )

    repo = task / "environment" / "repo"
    for pf in new_tests:
        name = Path(pf.path).name
        if name.startswith("eval_") or "verifier" in pf.path:
            continue  # already namespaced away from paths an agent would pick
        parent = (repo / pf.path).parent
        if not parent.is_dir():
            continue
        siblings = [q.name for q in parent.iterdir() if q.is_file()]
        tests = [q for q in siblings if TEST_PATH_HINT.search(q)]
        if len(siblings) - len(tests) > len(tests):
            r.warn(
                f"tests.patch creates {pf.path} in a directory that is mostly implementation "
                "code — an agent may create the same path and break patch application. Prefix "
                "the file with eval_ or move it to a verifier-only directory"
            )

    added = "\n".join("\n".join(pf.added) for pf in patch_files)
    for pattern, label in AUTO_FAIL:
        if re.search(pattern, added, re.MULTILINE):
            r.fail(f"tests.patch: Quality Check auto-REMOVE pattern — {label}")
    for pattern, label in SOURCE_SCAN:
        if re.search(pattern, added, re.MULTILINE):
            r.warn(f"tests.patch: possible unfaithful assertion — {label}")

    # Existence checks must be paired with a content or behaviour assertion.
    exists_hits = re.findall(r"[^\n]*\.(?:exists|is_file|isFile|Stat)\s*\([^\n]*", added)
    if exists_hits and not re.search(
        r"(read_text|readFileSync|ReadFile|content|body|json|stdout)", added
    ):
        r.warn(
            "tests.patch: existence checks with no content assertion nearby — touching the "
            "right filename would pass"
        )


def check_test_sh(task: Path, r: Result) -> None:
    path = task / "tests" / "test.sh"
    if not path.is_file():
        return
    text = read_text(path)
    if "/logs/verifier/reward.txt" not in text:
        r.warn("tests/test.sh never mentions /logs/verifier/reward.txt — Harbor reads the reward there")
    if "tests.patch" not in text:
        r.warn("tests/test.sh does not apply tests/tests.patch — the f2p tests may never be injected")


def check_stray_artifacts(task: Path, r: Result) -> None:
    hits: list[str] = []
    for path in task.rglob("*"):
        name = path.name
        if name in STRAY_NAMES or name.endswith(STRAY_SUFFIXES):
            rel = path.relative_to(task)
            if ".git/" in f"{rel}/" and name.endswith(("~", ".orig")):
                continue  # git internals legitimately use these suffixes
            hits.append(str(rel))
            if len(hits) > 20:
                break
    for hit in hits:
        r.fail(f"stray artifact caps the packaging axis at 1: {hit}")


def check_instruction(task: Path, r: Result, patch_files: list[PatchFile]) -> None:
    inst = task / "instruction.md"
    if not inst.is_file():
        return
    text = read_text(inst)
    low = text.lower()

    if re.search(r"github\.com/[^\s)]+/(pull|commit|issues)/", low):
        r.fail("instruction.md contains a source URL — that leaks the fix")
    if re.search(r"\b[0-9a-f]{40}\b", low):
        r.fail("instruction.md contains a 40-character commit SHA — leakage")
    if "where to look" in low:
        r.fail("instruction.md says 'where to look' — over-prescriptive")
    for phrase in ("the tests reference", "the test references", "tests.patch", "golden.patch",
                   "the verifier", "hidden test"):
        if phrase in low:
            r.fail(f"instruction.md exposes verifier internals: '{phrase}'")
    for phrase in ("the system shall", "it is required that", "as an ai", "this document"):
        if phrase in low:
            r.warn(f"instruction.md reads as templated/LLM-generated: '{phrase}'")

    # Naming a concrete test file is leakage, but telling the agent to leave
    # `*_test.go` alone is required when tests ship via tests.patch.
    filename = re.compile(r"[\w./-]+(?:_test\.\w+|\.test\.\w+)|test_[\w-]+\.py")
    for line in text.splitlines():
        if re.search(r"\b(do not|don't|never|avoid|without)\b", line, re.IGNORECASE):
            continue
        for hit in filename.findall(line):
            if hit.startswith(("*", "_", ".")) or "*" in hit:
                continue  # a glob, not a specific file
            r.warn(f"instruction.md names the test file '{hit}' — usually leakage")
            break

    # Standing rule: when tests ship via tests.patch, the instruction must tell the
    # agent not to write or edit test files, or trials collide with the patch.
    if any(p.is_new and TEST_PATH_HINT.search(p.path) for p in patch_files):
        if not re.search(r"(do not|don't|never)[^.\n]{0,60}(test|spec)", low):
            r.warn(
                "tests.patch ships new test files but instruction.md never tells the agent to "
                "leave test files alone — agent-authored tests collide with the patch"
            )


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("task_dir", type=Path, help="path to the unzipped task/ contents")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    args = ap.parse_args()

    task = args.task_dir.resolve()
    if not task.is_dir():
        print(f"ERROR: not a directory: {task}", file=sys.stderr)
        return 2

    patch = task / "tests" / "tests.patch"
    if patch.is_file():
        patch_files, facts = load_patch(patch)
    else:
        patch_files, facts = [], GitPatchFacts()

    r = Result()
    check_structure(task, r)
    check_instruction_sync(task, r)
    check_task_toml(task, r)
    check_config_json(task, r, patch_files)
    check_tests_patch(task, r, patch_files, facts)
    check_patch_applies(task, r)
    check_test_sh(task, r)
    check_stray_artifacts(task, r)
    check_instruction(task, r, patch_files)

    if not args.quiet:
        for note in r.notes:
            print(f"INFO  {note}")
        for warning in r.warnings:
            print(f"WARN  {warning}")
    for error in r.errors:
        print(f"FAIL  {error}")

    if args.strict and r.warnings and r.ok:
        print(f"FAIL  --strict: {len(r.warnings)} warning(s) treated as failures")
        return 1
    if r.ok:
        print(f"PASS  {task.name} — 0 failures, {len(r.warnings)} warning(s)")
        return 0
    print(f"FAIL  {task.name} — {len(r.errors)} failure(s), {len(r.warnings)} warning(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
