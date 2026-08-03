#!/usr/bin/env python3
"""Keep the workspace docs honest.

Some rules have to appear in more than one file: `AGENTS.md` and the Cursor rule
are always in context and must be self-contained, while the reference docs carry
the reasoning. Copies are therefore allowed, but silent disagreement is not —
a stale number is worse than no number, because it gets acted on.

This checks three things:

  1. Policy numbers in prose match the constants the tooling enforces
     (scripts/validate_task.py is the single source of truth).
  2. Every file path a doc points at exists, and shell scripts are executable.
  3. Each canonical rule owner named below still exists.

Put `<!-- policy-check: ignore -->` on a line to exempt it, which is what the
places that deliberately quote the hub's older wording do.

Run: python3 scripts/check-docs.py
Exit codes: 0 = consistent, 1 = drift found, 2 = bad usage.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

# Importing validate_task.py would otherwise leave scripts/__pycache__ behind,
# and this workspace treats stray artifacts as something to delete, not explain.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

# Where each rule is written out in full, with its reasoning. Copies elsewhere
# are summaries and must not contradict these files.
CANONICAL = {
    "fail-to-pass range, PR scope, oracle edits, verifiability": "docs/GUIDELINES.md",
    "task.toml schema and published limits": "docs/HARBOR-FORMAT.md",
    "revision budget and platform-vs-reviewer iteration": "docs/REVISION-BUDGET.md",
    "eval failure triage": "docs/PLATFORM-TRIAGE.md",
    "skip criteria": "docs/SKIP-GUIDE.md",
}

IGNORE = "policy-check: ignore"
SKIP_DIRS = {"hub-scrape", ".git", "tasks", ".preflight"}

# Prose that states the fail-to-pass range, in either word order.
F2P_RANGE = [
    re.compile(r"(\d{1,3})\s*[–—-]\s*(\d{1,3})\s*\**\s*(?:f2p|fail[-\s]to[-\s]pass)", re.I),
    re.compile(r"(?:f2p|fail[-\s]to[-\s]pass)\D{0,30}?(\d{1,3})\s*[–—-]\s*(\d{1,3})", re.I),
]

# Paths mentioned in backticks or markdown links.
PATH_IN_TICKS = re.compile(r"`(\.?/?(?:docs|scripts|templates)/[\w./+-]+)`")
PATH_IN_LINK = re.compile(r"\]\((\.?/?(?:docs|scripts|templates)/[\w./+-]+)\)")


def load_constants() -> dict:
    spec = importlib.util.spec_from_file_location("validate_task", ROOT / "scripts" / "validate_task.py")
    if spec is None or spec.loader is None:
        raise SystemExit("cannot import scripts/validate_task.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {
        "min_f2p": module.MIN_F2P,
        "max_f2p": module.MAX_F2P,
        "network_modes": module.NETWORK_MODES,
    }


def docs_to_scan() -> list[Path]:
    files = [ROOT / "AGENTS.md", ROOT / "README.md"]
    files += sorted((ROOT / ".cursor" / "rules").glob("*.mdc"))
    files += sorted((ROOT / "docs").glob("*.md"))
    files += sorted((ROOT / "templates").glob("*.md"))
    return [f for f in files if f.is_file()]


def live_lines(path: Path) -> list[tuple[int, str]]:
    """Numbered lines, minus historical records and explicitly exempt lines.

    The session log in EC-LEARNINGS.md records what the rules were at the time,
    so policy numbers below its heading are history, not claims.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    stop = len(lines)
    if path.name == "EC-LEARNINGS.md":
        for i, line in enumerate(lines):
            if re.match(r"#+\s*Session log", line, re.I):
                stop = i
                break
    return [
        (i + 1, line)
        for i, line in enumerate(lines[:stop])
        if IGNORE not in line
    ]


def check_policy_numbers(files: list[Path], const: dict, errors: list[str]) -> int:
    expected = (const["min_f2p"], const["max_f2p"])
    seen = 0
    for path in files:
        rel = path.relative_to(ROOT)
        for lineno, line in live_lines(path):
            for pattern in F2P_RANGE:
                m = pattern.search(line)
                if not m:
                    continue
                seen += 1
                found = (int(m.group(1)), int(m.group(2)))
                if found != expected:
                    errors.append(
                        f"{rel}:{lineno} states a fail-to-pass range of "
                        f"{found[0]}-{found[1]} but validate_task.py enforces "
                        f"{expected[0]}-{expected[1]}"
                    )
                break
    if seen == 0:
        errors.append(
            "no document states the fail-to-pass range — an agent reading only "
            "AGENTS.md would not know it"
        )
    return seen


def check_network_modes(files: list[Path], const: dict, errors: list[str]) -> None:
    """Every stated per-block network_mode must match what the validator requires."""
    pattern = re.compile(
        r"\[?(environment|agent|verifier)\]?[^\n`]{0,40}?network_mode\s*=?:?\s*[\"'`]?"
        r"(public|allowlist|no-network|none)",
        re.I,
    )
    for path in files:
        rel = path.relative_to(ROOT)
        for lineno, line in live_lines(path):
            for block, mode in pattern.findall(line):
                want = const["network_modes"][block.lower()]
                if mode.lower() != want:
                    errors.append(
                        f'{rel}:{lineno} says [{block.lower()}] network_mode = "{mode}" '
                        f'but the required value is "{want}"'
                    )


def check_paths(files: list[Path], errors: list[str]) -> int:
    seen = 0
    for path in files:
        rel = path.relative_to(ROOT)
        for lineno, line in live_lines(path):
            for match in list(PATH_IN_TICKS.finditer(line)) + list(PATH_IN_LINK.finditer(line)):
                ref = match.group(1)
                if "<" in ref or "*" in ref:
                    continue
                target = ROOT / ref.lstrip("./")
                seen += 1
                if not target.exists():
                    errors.append(f"{rel}:{lineno} points at {ref}, which does not exist")
                elif target.suffix == ".sh" and not target.stat().st_mode & 0o111:
                    errors.append(f"{rel}:{lineno} points at {ref}, which is not executable")
    return seen


def check_canonical(errors: list[str]) -> None:
    for rule, owner in CANONICAL.items():
        if not (ROOT / owner).is_file():
            errors.append(f"canonical owner for {rule} is missing: {owner}")


def main() -> int:
    if len(sys.argv) > 1:
        print(__doc__)
        return 2

    const = load_constants()
    files = docs_to_scan()
    errors: list[str] = []

    ranges = check_policy_numbers(files, const, errors)
    check_network_modes(files, const, errors)
    refs = check_paths(files, errors)
    check_canonical(errors)

    for error in errors:
        print(f"FAIL  {error}")
    if errors:
        print(f"\nFAIL  {len(errors)} inconsistency(ies) across {len(files)} document(s)")
        return 1
    print(
        f"PASS  {len(files)} document(s): {ranges} policy-number mention(s) agree with "
        f"validate_task.py, {refs} path reference(s) resolve"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
