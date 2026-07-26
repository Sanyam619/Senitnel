#!/usr/bin/env python3
"""Offline seal verification helper (authcheck is authoritative)."""
import subprocess
import sys
from pathlib import Path


def main() -> int:
    seal_path = Path("/data/token/session.seal")
    if not seal_path.exists():
        print("no seal file")
        return 1
    result = subprocess.run(
        ["/opt/pk11/bin/authcheck"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "accept" in result.stdout.lower():
        print(f"seal OK under gate: {seal_path.read_text().strip()}")
        return 0
    print("seal/gate rejected:", result.stdout + result.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
