#!/usr/bin/env python3
"""Self-test for the Sentinel toolchain.

Builds a minimal but genuinely valid Harbor task in a scratch directory, then
copies it once per defect case, injects one defect, and asserts the tooling
reports that defect. The clean case must come back with zero failures, which is
what stops a future edit from turning a check into a false positive — or into
silence.

Three suites:

  validator  scripts/validate_task.py against one defect per case, plus a
             coverage assertion that *every* auto-REMOVE pattern it knows about
             is exercised by some case — Go and JS and gtest included, not just
             the Python ones.
  shell      preflight.sh, zip-task.sh, git-hygiene.sh, sync-problem-statement.sh
             and ingest-task.sh, each asserted to reject what it claims to reject.
             These wrappers were the untested layer that hid a bogus "docker
             build failed" verdict.
  docs       scripts/check-docs.py against a mirrored doc tree with drift injected.

Run: python3 scripts/selftest.py [-v] [--keep] [--suite validator|shell|docs]
Exit codes: 0 = every case behaved, 1 = at least one case did not.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_task.py"
# Stops preflight.sh and zip-task.sh from re-entering this script.
CHILD_ENV = {**os.environ, "SENTINEL_SELFTEST": "1"}

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_AUTHOR_NAME": "fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.com",
    "GIT_COMMITTER_NAME": "fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.com",
}

APP_PY = '''"""Tiny module the fixture task builds on."""


def normalise(value):
    if value is None:
        raise ValueError("value is required")
    return str(value).strip().lower()


def parse_pair(text):
    if "=" not in text:
        raise ValueError(f"expected key=value, got {text!r}")
    key, _, value = text.partition("=")
    return normalise(key), value.strip()
'''

BASE_TEST_PY = '''from app import normalise, parse_pair


def test_base():
    assert normalise("  Hello ") == "hello"
    assert parse_pair("A = 1") == ("a", "1")
'''

DOCKERFILE = """FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pytest==8.2.0
COPY repo/ /app/
"""

INSTRUCTION = """# Support quoted values when parsing pairs

The pair parser currently treats everything after the first `=` as a literal
value, so quoted values keep their surrounding quotes and escaped separators are
split in the wrong place. Callers that round-trip configuration through the
parser therefore lose data.

Make the parser handle quoted values: a value wrapped in matching single or
double quotes should come back without the quotes, an escaped separator inside a
quoted value should stay part of the value, and an unterminated quote should
raise `ValueError` with a message naming the offending input. Unquoted values
must keep behaving exactly as they do today, including the existing trimming and
case-folding of keys.

Success criteria: quoted values round-trip without their quotes, escaped
separators survive, unterminated quotes raise `ValueError`, and existing
behaviour for unquoted input is unchanged.

Do not add, edit, or delete test files — the suite that grades this work is
supplied separately and any test files you create will be discarded.
"""

TEST_SH = """#!/usr/bin/env bash
set -euo pipefail

cd /app
git apply /verifier/tests.patch
mkdir -p /logs/verifier

if python -m pytest -q tests/ > /logs/verifier/pytest.log 2>&1; then
  echo "1.0" > /logs/verifier/reward.txt
else
  echo "0.0" > /logs/verifier/reward.txt
fi
"""

SOLVE_SH = """#!/usr/bin/env bash
set -euo pipefail

cd /app
git apply /solution/golden.patch
"""

TASK_TOML = """schema_version = "1.3"

[metadata]
author_name = "anonymous"
author_email = "anonymous@snorkel.ai"
category = "implementation"
subcategory = "feature"
coding_language = "python"
repo_name = "fixture"
repo_license = "MIT"
source_pr_url = "https://github.com/example/fixture/pull/1"
base_commit_sha = "{sha}"
model_difficulty = "medium"
difficulty_explanation = "fixture task used by scripts/selftest.py"
tags = ["fixture"]

[verifier]
timeout_sec = 300.0
network_mode = "no-network"

[agent]
timeout_sec = 7200.0
network_mode = "allowlist"
allowed_hosts = [
    "api.portkey.ai",
]

[environment]
build_timeout_sec = 900.0
cpus = 4
memory_mb = 8192
storage_mb = 10240
gpus = 0
network_mode = "public"
"""

N_TESTS = 12


def eval_test_source(*, skip_marker: bool = False, swallow: bool = False) -> str:
    """The fail-to-pass suite shipped through tests.patch."""
    cases = [
        'assert parse_pair(\'k="quoted"\') == ("k", "quoted")',
        "assert parse_pair(\"k='quoted'\") == (\"k\", \"quoted\")",
        'assert parse_pair(\'k="a=b"\') == ("k", "a=b")',
        'assert parse_pair(\'k="  spaced  "\') == ("k", "  spaced  ")',
        'assert parse_pair(\'K="v"\') == ("k", "v")',
        'assert parse_pair("k=plain") == ("k", "plain")',
        'assert parse_pair("k= plain ") == ("k", "plain")',
        'assert parse_pair(\'k=""\') == ("k", "")',
        'assert normalise("  Mixed Case ") == "mixed case"',
        'assert parse_pair(\'k="tail"extra\') == ("k", "tail")',
        'assert parse_pair(\'k="a\\\\"b"\') == ("k", \'a"b\')',
    ]
    body = ["import pytest\n\nfrom app import normalise, parse_pair\n"]
    for i, case in enumerate(cases[: N_TESTS - 1], start=1):
        decorator = '@pytest.mark.skip(reason="flaky")\n' if (skip_marker and i == 1) else ""
        body.append(f"{decorator}def test_feature_{i:02d}():\n    {case}\n")

    last = f"def test_feature_{N_TESTS:02d}():\n"
    if swallow:
        last += (
            "    try:\n"
            "        parse_pair('k=\"unterminated')\n"
            "    except ValueError:\n"
            "        pass\n"
        )
    else:
        last += (
            "    with pytest.raises(ValueError) as excinfo:\n"
            "        parse_pair('k=\"unterminated')\n"
            '    assert "unterminated" in str(excinfo.value)\n'
        )
    body.append(last)
    return "\n".join(body)


GOLDEN_APP_PY = APP_PY.replace(
    '''def parse_pair(text):
    if "=" not in text:
        raise ValueError(f"expected key=value, got {text!r}")
    key, _, value = text.partition("=")
    return normalise(key), value.strip()
''',
    '''QUOTES = ("'", '"')


def _split_key(text):
    if "=" not in text:
        raise ValueError(f"expected key=value, got {text!r}")
    key, _, value = text.partition("=")
    return key, value


def _read_quoted(value, quote, original):
    out = []
    escaped = False
    for index, char in enumerate(value[1:], start=1):
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\\\":
            escaped = True
            continue
        if char == quote:
            return "".join(out)
        out.append(char)
    raise ValueError(f"unterminated {quote} quote in {original!r}")


def parse_value(value, original):
    stripped = value.strip()
    if stripped[:1] in QUOTES:
        return _read_quoted(stripped, stripped[0], original)
    return stripped


def parse_pair(text):
    key, value = _split_key(text)
    return normalise(key), parse_value(value, text)


def parse_pairs(lines):
    """Parse many pairs, skipping blank lines and comments."""
    out = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, value = parse_pair(stripped)
        out[key] = value
    return out


def format_pair(key, value):
    """Inverse of parse_pair, quoting only when necessary."""
    needs_quotes = value != value.strip() or "=" in value or not value
    if needs_quotes:
        escaped = value.replace("\\\\", "\\\\\\\\").replace('"', '\\\\"')
        return f'{normalise(key)}="{escaped}"'
    return f"{normalise(key)}={value}"


def round_trip(text):
    """Parse then re-format, used by the config loader to canonicalise input."""
    key, value = parse_pair(text)
    return format_pair(key, value)
''',
)

GOLDEN_HELPER_PY = '''"""Config loading built on the pair parser."""

from app import parse_pairs, round_trip


class ConfigError(ValueError):
    """Raised when a config document cannot be parsed."""


def load(text):
    try:
        return parse_pairs(text.splitlines())
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def canonicalise(text):
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
            continue
        out.append(round_trip(stripped))
    return "\\n".join(out)


def merge(base, override):
    merged = dict(base)
    for key, value in override.items():
        if value is not None:
            merged[key] = value
    return merged
'''


# --------------------------------------------------------------------------- #
# fixture construction
# --------------------------------------------------------------------------- #
def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, env=GIT_ENV,
        capture_output=True, text=True, check=True,
    )
    return proc.stdout


def write(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def make_patch(repo: Path, out: Path, mutate) -> None:
    """Stage what `mutate` writes, capture it as a diff, restore the repo."""
    mutate(repo)
    git(repo, "add", "-A")
    write(out, git(repo, "diff", "--cached"))
    git(repo, "reset", "--hard", "--quiet")
    git(repo, "clean", "-fdq")


def build_template(dest: Path) -> Path:
    """A task that should pass validation with zero failures."""
    task = dest / "fixture-task"
    repo = task / "environment" / "repo"
    repo.mkdir(parents=True)

    # An empty template keeps git from installing sample hooks, which some
    # sandboxes refuse to create.
    with tempfile.TemporaryDirectory() as empty:
        git(repo, "init", "--quiet", f"--template={empty}", ".")
    write(repo / "app.py", APP_PY)
    write(repo / "tests" / "test_app.py", BASE_TEST_PY)
    write(repo / "README.md", "# fixture\n\nA repo that exists only for selftest.py.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "fixture base")
    sha = git(repo, "rev-parse", "HEAD").strip()

    def golden(r: Path) -> None:
        write(r / "app.py", GOLDEN_APP_PY)
        write(r / "config.py", GOLDEN_HELPER_PY)

    make_patch(repo, task / "solution" / "golden.patch", golden)
    make_patch(
        repo,
        task / "tests" / "tests.patch",
        lambda r: write(r / "tests" / "eval_feature.py", eval_test_source()),
    )

    write(task / "instruction.md", INSTRUCTION)
    write(task / "environment" / "problem_statement.md", INSTRUCTION)
    write(task / "environment" / "Dockerfile", DOCKERFILE)
    write(task / "solution" / "solve.sh", SOLVE_SH, executable=True)
    write(task / "tests" / "test.sh", TEST_SH, executable=True)
    write(task / "task.toml", TASK_TOML.format(sha=sha))
    write(task / "tests" / "config.json", json.dumps(config_json(), indent=2) + "\n")
    # Building the patches wrote reflog entries; a shipped task must have none.
    shutil.rmtree(repo / ".git" / "logs", ignore_errors=True)
    return task


def config_json() -> dict:
    return {
        "execution": {"commands": ["python -m pytest -q tests/"]},
        "grading": {
            "fail_to_pass": [
                f"tests/eval_feature.py::test_feature_{i:02d}" for i in range(1, N_TESTS + 1)
            ],
            "pass_to_pass": ["tests/test_app.py::test_base"],
            "allow_extra_failures": False,
            "parser": {"framework": "pytest"},
        },
        "artifacts": {"reward": "/logs/verifier/reward.txt"},
    }


# --------------------------------------------------------------------------- #
# defect injections
# --------------------------------------------------------------------------- #
def edit_config(task: Path, mutate) -> None:
    path = task / "tests" / "config.json"
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def edit_text(task: Path, rel: str, old: str, new: str, *, count: int = 1) -> None:
    path = task / rel
    text = path.read_text()
    if old not in text:
        raise AssertionError(f"selftest bug: {old!r} not in {rel}")
    path.write_text(text.replace(old, new) if count < 0 else text.replace(old, new, count))


def regen_tests_patch(task: Path, files: dict[str, str]) -> None:
    def mutate(repo: Path) -> None:
        for rel, content in files.items():
            write(repo / rel, content)

    make_patch(task / "environment" / "repo", task / "tests" / "tests.patch", mutate)


def patch_files(extra: dict[str, str] | None = None, python_extra: str = "") -> dict[str, str]:
    """The shipped suite, optionally with extra files or extra Python appended."""
    files = {"tests/eval_feature.py": eval_test_source() + python_extra}
    files.update(extra or {})
    return files


def append_to_instruction(task: Path, extra: str) -> None:
    for rel in ("instruction.md", "environment/problem_statement.md"):
        path = task / rel
        path.write_text(path.read_text() + extra)


# --------------------------------------------------------------------------- #
# One case per auto-REMOVE / unfaithful-assertion pattern, in the language that
# pattern belongs to. The four real tasks in this workspace are Go, TypeScript
# and C++; a Python-only suite would leave those regexes unwatched.
# --------------------------------------------------------------------------- #
GO_HEAD = 'package feature\n\nimport "testing"\n\n'
JS_HEAD = 'import { describe, it, expect } from "vitest";\n\nimport { parsePair } from "../app";\n\n'
CC_HEAD = '#include <gtest/gtest.h>\n\n#include "parser.h"\n\n'

PATTERN_CASES: list[tuple[str, dict[str, str] | None, str, str]] = [
    # name, extra files, python appended to the shipped suite, expected label
    ("pattern_pytest_skipif", None,
     '\n@pytest.mark.skipif(True, reason="not yet")\ndef test_later():\n    assert parse_pair("k=v")\n',
     "silent skip (@pytest.mark.skipif)"),
    ("pattern_importorskip", None,
     '\ndef test_optional():\n    yaml = pytest.importorskip("yaml")\n    assert yaml is not None\n',
     "silent skip (pytest.importorskip)"),
    ("pattern_pytest_skip_call", None,
     '\ndef test_deferred():\n    pytest.skip("comes back later")\n',
     "silent skip (pytest.skip)"),
    ("pattern_unittest_skip", None,
     '\nimport unittest\n\n\nclass Legacy(unittest.TestCase):\n'
     '    @unittest.skip("ported already")\n    def test_old(self):\n        pass\n',
     "silent skip (unittest.skip)"),
    ("pattern_import_error", None,
     '\ntry:\n    import fastjson\nexcept ImportError:\n    fastjson = None\n',
     "silent skip (ImportError swallowed)"),
    ("pattern_inline_except_pass", None,
     '\ndef test_tolerant():\n    try:\n        parse_pair("nope")\n'
     '    except ValueError: pass\n',
     "fail-open (except ... pass)"),
    ("pattern_exists_guard", None,
     '\nfrom pathlib import Path\n\n\ndef test_report():\n'
     '    report = Path("report.txt")\n    if not report.exists(): return\n'
     '    assert report.stat().st_size > 0\n',
     "fail-open (exists guard returns)"),
    ("pattern_continue_skip", None,
     '\ndef test_batch():\n    for case in ["k=v", "bad"]:\n'
     '        if "=" not in case:\n            continue  # skip\n'
     '        assert parse_pair(case)\n',
     "fail-open (silently continues)"),

    ("pattern_go_skip",
     {"tests/eval_quoted_test.go": GO_HEAD +
      'func TestQuotedValue(t *testing.T) {\n\tt.Skip("flaky on CI")\n}\n'},
     "", "silent skip (Go t.Skip)"),
    ("pattern_go_testing_short",
     {"tests/eval_short_test.go": GO_HEAD +
      'func TestQuotedValueShort(t *testing.T) {\n\tif testing.Short() {\n'
      '\t\treturn\n\t}\n}\n'},
     "", "conditional skip (Go testing.Short)"),

    ("pattern_js_skip",
     {"tests/eval_quoted.test.ts": JS_HEAD +
      'it.skip("keeps quoted values", () => {\n'
      '  expect(parsePair(\'k="v"\')).toEqual(["k", "v"]);\n});\n'},
     "", "silent skip (JS .skip)"),
    ("pattern_js_xit",
     {"tests/eval_xit.test.ts": JS_HEAD +
      'xit("keeps quoted values", () => {\n'
      '  expect(parsePair(\'k="v"\')).toEqual(["k", "v"]);\n});\n'},
     "", "silent skip (JS xit/xdescribe)"),
    ("pattern_js_only",
     {"tests/eval_only.test.ts": JS_HEAD +
      'it.only("keeps quoted values", () => {\n'
      '  expect(parsePair(\'k="v"\')).toEqual(["k", "v"]);\n});\n'},
     "", "coverage shrink (JS .only skips siblings)"),
    ("pattern_empty_catch",
     {"tests/eval_catch.test.ts": JS_HEAD +
      'it("tolerates anything", () => {\n  try {\n'
      '    parsePair(\'k="unterminated\');\n  } catch (err) {}\n});\n'},
     "", "fail-open (empty catch block)"),

    ("pattern_gtest_skip",
     {"tests/eval_quoted_test.cc": CC_HEAD +
      'TEST(ParserTest, QuotedValue) {\n  GTEST_SKIP();\n}\n'},
     "", "silent skip (GTEST_SKIP)"),
    ("pattern_gtest_disabled",
     {"tests/eval_disabled_test.cc": CC_HEAD +
      'TEST(ParserTest, DISABLED_QuotedValue) {\n'
      '  EXPECT_EQ(ParsePair("k=\\"v\\"").second, "v");\n}\n'},
     "", "silent skip (gtest DISABLED_)"),
]

# Unfaithful assertions warn rather than fail — they need judgement, not a veto.
SOURCE_SCAN_CASES: list[tuple[str, dict[str, str] | None, str, str]] = [
    ("scan_reads_source_text",
     {"tests/eval_source.test.ts": JS_HEAD +
      'import { readFileSync } from "fs";\n\n'
      'it("implements the parser", () => {\n'
      '  const src = readFileSync("app.ts", "utf8"); expect(src).toContain("parseValue");\n});\n'},
     "", "asserts on file contents read as text"),
    ("scan_substring_of_source", None,
     '\ndef test_implementation():\n    source = open("app.py").read()\n'
     '    assert "parse_value" in source\n',
     "asserts substring of source code"),
    ("scan_shells_out_to_grep", None,
     '\nimport subprocess\n\n\ndef test_defined():\n'
     '    subprocess.run(["grep", "-q", "parse_value", "app.py"], check=True)\n',
     "shells out to grep instead of running code"),
]


def pattern_case(extra: dict[str, str] | None, python_extra: str):
    return lambda t: regen_tests_patch(t, patch_files(extra, python_extra))


def _shrink_hunk(task: Path) -> None:
    """Understate a hunk's added-line count, which git applies without complaint."""
    path = task / "tests" / "tests.patch"
    text = path.read_text()
    new, count = re.subn(
        r"@@ -0,0 \+1,(\d+) @@",
        lambda m: f"@@ -0,0 +1,{int(m.group(1)) - 2} @@",
        text,
        count=1,
    )
    if count != 1:
        raise AssertionError("selftest bug: no new-file hunk header to shrink")
    path.write_text(new)


CASES: list[tuple[str, object, str | None]] = [
    ("clean", None, None),

    # fail-to-pass contract
    ("f2p_too_few",
     lambda t: edit_config(t, lambda d: d["grading"].__setitem__(
         "fail_to_pass", d["grading"]["fail_to_pass"][:9])),
     "9 fail_to_pass tests"),
    ("f2p_too_many",
     lambda t: edit_config(t, lambda d: d["grading"].__setitem__(
         "fail_to_pass", d["grading"]["fail_to_pass"] + [
             f"tests/eval_feature.py::test_extra_{i}" for i in range(9)])),
     "keep it at or below 20"),
    ("f2p_duplicate",
     lambda t: edit_config(t, lambda d: d["grading"].__setitem__(
         "fail_to_pass", d["grading"]["fail_to_pass"][:-1] + [
             d["grading"]["fail_to_pass"][0]])),
     "duplicate ids"),
    ("f2p_overlaps_p2p",
     lambda t: edit_config(t, lambda d: d["grading"].__setitem__(
         "pass_to_pass", [d["grading"]["fail_to_pass"][0]])),
     "in both fail_to_pass and pass_to_pass"),
    ("f2p_ids_unmatched",
     lambda t: edit_config(t, lambda d: d["grading"].__setitem__(
         "fail_to_pass", [f"tests/ghost.py::test_absent_{i:02d}" for i in range(1, 13)])),
     "can be found in tests/tests.patch"),

    # tests.patch integrity
    ("corrupt_hunk_header", _shrink_hunk, "corrupt hunk header"),
    ("patch_collides_with_existing_file",
     lambda t: edit_text(
         t, "tests/tests.patch", "tests/eval_feature.py", "tests/test_app.py", count=-1),
     "does not apply to environment/repo"),
    ("patch_deletes_existing_test",
     lambda t: make_patch(
         t / "environment" / "repo", t / "tests" / "tests.patch",
         lambda r: (r / "tests" / "test_app.py").unlink()),
     "never remove existing tests"),
    ("skip_marker",
     lambda t: regen_tests_patch(t, {"tests/eval_feature.py": eval_test_source(skip_marker=True)}),
     "silent skip (@pytest.mark.skip)"),
    ("swallowed_exception",
     lambda t: regen_tests_patch(t, {"tests/eval_feature.py": eval_test_source(swallow=True)}),
     "fail-open (except ... pass)"),

    # task.toml
    ("verifier_network_public",
     lambda t: edit_text(t, "task.toml", 'network_mode = "no-network"', 'network_mode = "public"'),
     'must be "no-network"'),
    ("cpus_out_of_range",
     lambda t: edit_text(t, "task.toml", "cpus = 4", "cpus = 8"),
     "allowed values are 2 or 4"),
    ("memory_out_of_range",
     lambda t: edit_text(t, "task.toml", "memory_mb = 8192", "memory_mb = 262144"),
     "must be between 2048 and 16384"),
    ("gpus_requested",
     lambda t: edit_text(t, "task.toml", "gpus = 0", "gpus = 1"),
     "gpus = 1"),
    ("portkey_missing",
     lambda t: edit_text(t, "task.toml", '    "api.portkey.ai",\n', ""),
     "api.portkey.ai"),
    ("toml_invalid",
     lambda t: edit_text(t, "task.toml", 'schema_version = "1.3"', "schema_version ="),
     "not valid TOML"),
    ("source_url_missing",
     lambda t: edit_text(
         t, "task.toml", 'source_pr_url = "https://github.com/example/fixture/pull/1"', ""),
     "needs a source URL"),

    # instruction
    ("instruction_desync",
     lambda t: (t / "instruction.md").write_text(
         (t / "instruction.md").read_text() + "\nOne more paragraph.\n"),
     "instruction.md != environment/problem_statement.md"),
    ("instruction_leaks_pr_url",
     lambda t: append_to_instruction(
         t, "\nSee https://github.com/example/fixture/pull/1 for context.\n"),
     "contains a source URL"),
    ("instruction_leaks_sha",
     lambda t: append_to_instruction(
         t, "\nStart from " + "a" * 40 + " and work forward.\n"),
     "commit SHA"),
    ("instruction_exposes_verifier",
     lambda t: append_to_instruction(t, "\nThe hidden test suite grades this.\n"),
     "verifier internals"),

    # packaging
    ("stray_artifact",
     lambda t: write(t / "environment" / "repo" / ".DS_Store", "junk"),
     "stray artifact"),
    ("pycache_shipped",
     lambda t: write(t / "environment" / "repo" / "__pycache__" / "app.cpython-311.pyc", "x"),
     "stray artifact"),
    ("runs_dir_shipped",
     lambda t: (t / "runs" / "trial-1").mkdir(parents=True),
     "runs/ is inside the task directory"),
    ("golden_patch_missing",
     lambda t: (t / "solution" / "golden.patch").unlink(),
     "missing solution/golden.patch"),
    ("legacy_solution_patch_name",
     lambda t: (t / "solution" / "golden.patch").rename(t / "solution" / "solution.patch"),
     "rename it to solution/golden.patch"),
    ("required_file_missing",
     lambda t: (t / "tests" / "test.sh").unlink(),
     "missing required file: tests/test.sh"),
    ("repo_git_missing",
     lambda t: shutil.rmtree(t / "environment" / "repo" / ".git"),
     "missing environment/repo/.git"),
]

CASES += [
    (name, pattern_case(extra, python_extra), label)
    for name, extra, python_extra, label in PATTERN_CASES
]
CASES += [
    (name, pattern_case(extra, python_extra), ("WARN", label))
    for name, extra, python_extra, label in SOURCE_SCAN_CASES
]


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #
def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd, cwd=cwd, env=env or CHILD_ENV, capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def run_validator(task: Path) -> tuple[int, str]:
    return run([sys.executable, str(VALIDATOR), str(task)])


def indent(text: str) -> str:
    return "\n".join(f"        {line}" for line in text.strip().splitlines())


class Report:
    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose
        self.failures: list[str] = []
        self.passed = 0
        self.skipped: list[str] = []

    def ok(self, name: str, detail: str) -> None:
        self.passed += 1
        print(f"ok    {name}: {detail}")

    def bad(self, name: str, detail: str) -> None:
        self.failures.append(f"{name}: {detail}")

    def skip(self, name: str, why: str) -> None:
        self.skipped.append(name)
        print(f"skip  {name}: {why}")

    def expect(self, name: str, condition: bool, detail: str, ok_detail: str) -> bool:
        if condition:
            self.ok(name, ok_detail)
        else:
            self.bad(name, detail)
        return condition


def validator_suite(template: Path, scratch: Path, report: Report, only: str | None) -> None:
    cases = [c for c in CASES if not only or c[0] == only]
    seen_labels: set[str] = set()

    for name, mutate, expected in cases:
        work = scratch / "cases" / name
        work.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(template, work, symlinks=True)
        if mutate is not None:
            mutate(work)
        code, out = run_validator(work)
        if report.verbose:
            print(f"--- {name} (exit {code})\n{out}")

        kind, needle = ("FAIL", expected) if isinstance(expected, str) else (
            expected if expected else (None, None)
        )
        if needle is not None:
            seen_labels.add(needle)

        if kind is None:
            report.expect(
                name, code == 0,
                f"expected a clean pass, got:\n{indent(out)}", "validates clean",
            )
        elif kind == "WARN":
            warned = any(needle in line for line in out.splitlines() if line.startswith("WARN"))
            report.expect(
                name, code == 0 and warned,
                f"expected a warning containing {needle!r}, got:\n{indent(out)}",
                f"warns {needle!r}",
            )
        elif code == 0:
            report.bad(name, "defect not caught — validator passed the task")
        else:
            report.expect(
                name, needle in out,
                f"caught something else, not {needle!r}:\n{indent(out)}", f"caught {needle!r}",
            )

    if only:
        return

    # Every pattern the validator knows about must be exercised by some case.
    # Adding a pattern without a case is how a check quietly rots.
    validate_task = load_validator_module()
    known = [label for _, label in validate_task.AUTO_FAIL + validate_task.SOURCE_SCAN]
    unexercised = sorted({label for label in known if label not in seen_labels})
    report.expect(
        "pattern_coverage", not unexercised,
        f"{len(unexercised)} pattern(s) have no case: {unexercised}",
        f"all {len(set(known))} auto-REMOVE / unfaithful patterns have a case",
    )


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_task", VALIDATOR)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# --------------------------------------------------------------------------- #
# shell suite — the wrappers that actually gate an upload
# --------------------------------------------------------------------------- #
def fresh(template: Path, scratch: Path, name: str) -> Path:
    work = scratch / "shell" / name
    work.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, work, symlinks=True)
    return work


def extra_commit_on_head(task: Path) -> None:
    repo = task / "environment" / "repo"
    write(repo / "scratch_note.py", "NOTE = 'left behind'\n")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "work in progress")
    shutil.rmtree(repo / ".git" / "logs", ignore_errors=True)


def leaked_tag(task: Path) -> None:
    """A commit reachable from a tag but not from HEAD — a real shipping mistake."""
    repo = task / "environment" / "repo"
    base = git(repo, "rev-parse", "HEAD").strip()
    write(repo / "scratch_note.py", "NOTE = 'left behind'\n")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "work in progress")
    git(repo, "tag", "wip")
    git(repo, "reset", "--hard", "--quiet", base)
    shutil.rmtree(repo / ".git" / "logs", ignore_errors=True)


def shell_suite(template: Path, scratch: Path, report: Report) -> None:
    hygiene = str(ROOT / "scripts" / "git-hygiene.sh")
    preflight = str(ROOT / "scripts" / "preflight.sh")
    zipper = str(ROOT / "scripts" / "zip-task.sh")
    syncer = str(ROOT / "scripts" / "sync-problem-statement.sh")

    # --- git-hygiene.sh ---------------------------------------------------- #
    work = fresh(template, scratch, "hygiene_clean")
    code, out = run([hygiene, str(work)])
    report.expect(
        "hygiene_clean", code == 0,
        f"clean fixture should pass git hygiene:\n{indent(out)}", "clean repo passes",
    )

    checks = [
        ("hygiene_dirty_tree",
         lambda w: write(w / "environment" / "repo" / "app.py", "print('edited')\n"),
         "dirty working tree"),
        # A commit on HEAD's own branch is invisible to `rev-list --all --not HEAD`;
        # what catches it is HEAD no longer matching base_commit_sha.
        ("hygiene_extra_commit_on_head", extra_commit_on_head, "base_commit_sha"),
        # A commit parked on another ref is what that check does cover.
        ("hygiene_leaked_tag", leaked_tag, "leaked commits"),
        ("hygiene_remote",
         lambda w: git(
             w / "environment" / "repo", "remote", "add", "origin",
             "https://github.com/example/fixture.git"),
         "remotes configured"),
        ("hygiene_sha_mismatch",
         lambda w: edit_text(
             w, "task.toml", 'base_commit_sha = "', 'base_commit_sha = "0000000'),
         "base_commit_sha"),
        ("hygiene_reflog",
         lambda w: write(w / "environment" / "repo" / ".git" / "logs" / "HEAD", "reflog\n"),
         "reflog present"),
        ("hygiene_patch_does_not_apply",
         lambda w: edit_text(
             w, "tests/tests.patch", "tests/eval_feature.py", "tests/test_app.py", count=-1),
         "does not apply"),
    ]
    for name, mutate, needle in checks:
        work = fresh(template, scratch, name)
        mutate(work)
        code, out = run([hygiene, str(work)])
        report.expect(
            name, code != 0 and needle in out,
            f"expected failure containing {needle!r}, got exit {code}:\n{indent(out)}",
            f"rejects: {needle}",
        )

    # --- preflight.sh ------------------------------------------------------ #
    work = fresh(template, scratch, "preflight_clean")
    code, out = run([preflight, str(work), "--fast"])
    report.expect(
        "preflight_clean", code == 0 and "SKIP  invoked from" in out,
        f"clean fixture should pass --fast preflight:\n{indent(out)}", "clean task passes --fast",
    )

    work = fresh(template, scratch, "preflight_rejects")
    edit_config(work, lambda d: d["grading"].__setitem__(
        "fail_to_pass", d["grading"]["fail_to_pass"][:4]))
    code, out = run([preflight, str(work), "--fast"])
    report.expect(
        "preflight_rejects", code != 0,
        f"preflight passed a task with 4 f2p tests:\n{indent(out)}", "fails on a bad task",
    )

    # Regression test for the tag that ended on a hyphen and produced a bogus
    # "docker build failed" verdict against a task that builds fine.
    tag_re = re.compile(r"^[a-z0-9]+([._-][a-z0-9]+)*$")
    for label, dirname in (
        ("preflight_image_tag_truncated", "7f0d2832-75ad-4bde-a511-6de29f4e5b1a_submission"),
        ("preflight_image_tag_odd_name", "Task Name (v2)!!"),
    ):
        work = scratch / "shell" / label / dirname
        work.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(template, work, symlinks=True)
        code, out = run([preflight, str(work), "--print-image"])
        tag = out.strip().splitlines()[-1] if out.strip() else ""
        report.expect(
            label, code == 0 and bool(tag_re.match(tag)),
            f"derived docker tag {tag!r} is not a valid reference", f"tag {tag!r} is valid",
        )

    # The rubric judge needs an Anthropic key. Assert preflight says exactly that
    # instead of running the judge and reporting a vague failure 20 seconds later.
    if shutil.which("harbor") is None:
        report.skip("rubric_requires_credentials", "harbor CLI not installed")
    else:
        work = fresh(template, scratch, "rubric_no_key")
        keyless = {k: v for k, v in CHILD_ENV.items() if k != "ANTHROPIC_API_KEY"}
        code, out = run([preflight, str(work), "--fast", "--rubric"], env=keyless)
        report.expect(
            "rubric_requires_credentials",
            code == 0 and "ANTHROPIC_API_KEY is not set" in out and "export ANTHROPIC_API_KEY" in out,
            f"expected a warning naming the missing key, got exit {code}:\n{indent(out)}",
            "names the missing credential instead of failing opaquely",
        )

    # --- zip-task.sh ------------------------------------------------------- #
    if shutil.which("zip") is None or shutil.which("unzip") is None:
        report.skip("zip_suite", "zip/unzip not on PATH")
    else:
        work = fresh(template, scratch, "zip_clean")
        out_zip = scratch / "shell" / "zip_clean.zip"
        code, out = run([zipper, str(work), str(out_zip)])
        if report.expect(
            "zip_clean", code == 0 and out_zip.is_file(),
            f"clean fixture should zip:\n{indent(out)}", "packs a clean task",
        ):
            listing = subprocess.run(
                ["unzip", "-l", str(out_zip)], capture_output=True, text=True, check=False,
            ).stdout
            report.expect(
                "zip_layout",
                " instruction.md" in listing and "refs/" in listing and " task/" not in listing,
                f"archive is not flat or lost git refs:\n{indent(listing)}",
                "archive is flat and keeps .git refs",
            )
            report.expect(
                "zip_not_inside_task", not list(work.glob("*.zip")),
                "the archive was written inside the task directory",
                "archive is written outside the task",
            )

        zip_checks = [
            ("zip_refuses_runs", lambda w: (w / "runs").mkdir(), "runs/ is inside"),
            ("zip_refuses_stray", lambda w: write(w / "tests" / ".DS_Store", "junk"), "stray artifacts"),
            ("zip_refuses_invalid_task",
             lambda w: edit_config(w, lambda d: d["grading"].__setitem__(
                 "fail_to_pass", d["grading"]["fail_to_pass"][:4])),
             "validate_task.py failed"),
            ("zip_refuses_dirty_repo",
             lambda w: write(w / "environment" / "repo" / "app.py", "print('edited')\n"),
             "dirty working tree"),
        ]
        for name, mutate, needle in zip_checks:
            work = fresh(template, scratch, name)
            target = scratch / "shell" / f"{name}.zip"
            mutate(work)
            code, out = run([zipper, str(work), str(target)])
            report.expect(
                name, code != 0 and needle in out and not target.exists(),
                f"expected refusal containing {needle!r}, got exit {code}:\n{indent(out)}",
                f"refuses: {needle}",
            )

    # --- sync-problem-statement.sh ----------------------------------------- #
    work = fresh(template, scratch, "sync")
    inst = work / "instruction.md"
    inst.write_text(inst.read_text() + "\nA late clarification.\n")
    before, _ = run_validator(work)
    code, _ = run([syncer, str(work)])
    after, out = run_validator(work)
    report.expect(
        "sync_problem_statement",
        before != 0 and code == 0 and after == 0,
        f"sync did not repair the desync (before={before}, sync={code}, after={after}):\n{indent(out)}",
        "repairs an instruction/problem_statement desync",
    )

    # --- ingest-task.sh ---------------------------------------------------- #
    ingest_suite(template, scratch, report)


def ingest_suite(template: Path, scratch: Path, report: Report) -> None:
    """Round-trip a zip through tasks/inbox → tasks/active, then clean up.

    This one touches the real workspace folders, so it uses an obviously-scoped
    name and removes both sides in a finally block.
    """
    if shutil.which("zip") is None:
        report.skip("ingest_round_trip", "zip not on PATH")
        return

    name = f"selftest-ingest-{os.getpid()}"
    inbox = ROOT / "tasks" / "inbox" / f"{name}.zip"
    active = ROOT / "tasks" / "active" / name
    try:
        work = fresh(template, scratch, "ingest")
        code, out = run([str(ROOT / "scripts" / "zip-task.sh"), str(work), str(inbox)])
        if code != 0:
            report.bad("ingest_round_trip", f"could not build the input zip:\n{indent(out)}")
            return
        code, out = run([str(ROOT / "scripts" / "ingest-task.sh"), f"{name}.zip"])
        report.expect(
            "ingest_round_trip",
            code == 0 and (active / "instruction.md").is_file()
            and (active / "environment" / "repo" / ".git").exists(),
            f"ingest did not unpack a usable task:\n{indent(out)}",
            "unpacks inbox zip into tasks/active with .git intact",
        )
    finally:
        inbox.unlink(missing_ok=True)
        shutil.rmtree(active, ignore_errors=True)
        shutil.rmtree(ROOT / "tasks" / "active" / f"{name}_runs", ignore_errors=True)


# --------------------------------------------------------------------------- #
# docs suite — check-docs.py against a mirrored tree with drift injected
# --------------------------------------------------------------------------- #
def mirror_docs(dest: Path) -> Path:
    """A faithful copy of everything check-docs.py reads (~360 KB), so that a
    reference resolving in the real tree also resolves in the mirror."""
    root = dest / "mirror"
    root.mkdir(parents=True)
    for rel in ("AGENTS.md", "README.md"):
        shutil.copy2(ROOT / rel, root / rel)
    for sub in ("scripts", "docs", "templates", ".cursor"):
        shutil.copytree(ROOT / sub, root / sub, symlinks=True)
    return root


def docs_suite(scratch: Path, report: Report) -> None:
    mirror = mirror_docs(scratch)
    checker = [sys.executable, str(mirror / "scripts" / "check-docs.py")]

    code, out = run(checker)
    if not report.expect(
        "docs_mirror_clean", code == 0,
        f"the mirrored doc tree does not pass:\n{indent(out)}", "mirrored docs pass",
    ):
        return

    module = load_validator_module()
    stale = f"{module.MIN_F2P - 1}\u2013{module.MAX_F2P}"
    agents = mirror / "AGENTS.md"
    original = agents.read_text()
    agents.write_text(original.replace(
        f"**{module.MIN_F2P}\u2013{module.MAX_F2P}** fail-to-pass", f"**{stale}** fail-to-pass", 1))
    code, out = run(checker)
    report.expect(
        "docs_detects_stale_number",
        code != 0 and "fail-to-pass range" in out,
        f"a stale f2p range in AGENTS.md was not detected:\n{indent(out)}",
        "detects a stale policy number",
    )
    agents.write_text(original)

    readme = mirror / "README.md"
    readme.write_text(readme.read_text() + "\nSee `scripts/does-not-exist.sh`.\n")
    code, out = run(checker)
    report.expect(
        "docs_detects_dead_reference",
        code != 0 and "does not exist" in out,
        f"a dead script reference was not detected:\n{indent(out)}",
        "detects a dead file reference",
    )


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-v", "--verbose", action="store_true", help="print tool output")
    ap.add_argument("--keep", action="store_true", help="keep the scratch directory")
    ap.add_argument("--only", help="run one validator case by name")
    ap.add_argument(
        "--suite", choices=("all", "validator", "shell", "docs"), default="all",
        help="run a single suite",
    )
    args = ap.parse_args()

    if shutil.which("git") is None:
        print("SKIP  selftest needs git on PATH")
        return 0

    scratch = Path(tempfile.mkdtemp(prefix="sentinel-selftest-"))
    report = Report(args.verbose)
    try:
        template = build_template(scratch)
        code, out = run_validator(template)
        if code != 0:
            print("FAIL  the clean fixture does not validate — the fixture or a check is wrong")
            print(out)
            return 1

        if args.only:
            validator_suite(template, scratch, report, args.only)
        else:
            if args.suite in ("all", "validator"):
                validator_suite(template, scratch, report, None)
            if args.suite in ("all", "shell"):
                shell_suite(template, scratch, report)
            if args.suite in ("all", "docs"):
                docs_suite(scratch, report)
    finally:
        if args.keep:
            print(f"kept  {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)

    total = report.passed + len(report.failures)
    if report.failures:
        print()
        for failure in report.failures:
            print(f"FAIL  {failure}")
        print(f"\nFAIL  {len(report.failures)} of {total} case(s) misbehaved")
        return 1
    skipped = f", {len(report.skipped)} skipped" if report.skipped else ""
    print(f"\nPASS  {total} case(s): every injected defect was caught{skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
