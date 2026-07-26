#!/usr/bin/env python3
"""Generic SHA-256 helper used by ops tooling."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: str | Path) -> str:
    return sha256_hex(Path(path).read_bytes())


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: digest_util.py PATH")
    print(file_sha256(sys.argv[1]))


if __name__ == "__main__":
    main()
