#!/usr/bin/env python3
"""Small digest helper used by ops notes; not part of the agent fix path."""

from __future__ import annotations

import hashlib
import sys


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    data = sys.stdin.read()
    sys.stdout.write(digest_text(data) + "\n")


if __name__ == "__main__":
    main()
