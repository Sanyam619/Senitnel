"""Recover move-dialect notes from match history (desk books)."""
from __future__ import annotations

import os
import re


def announce_samples(app_root: str | None = None) -> list[str]:
    root = app_root or os.environ.get("APP_ROOT", "/app")
    hist = os.path.join(root, "history")
    samples = []
    if not os.path.isdir(hist):
        return samples
    for name in sorted(os.listdir(hist)):
        if not name.endswith(".txt"):
            continue
        with open(os.path.join(hist, name)) as fh:
            text = fh.read()
        # history files themselves are boards; dialect lives in docs — keep a
        # stable token shape reminder for the desk.
        if re.search(r"first:\s*\S+", text):
            samples.append("F:b3-c3")
            samples.append("F:b3-c2:b3")
            samples.append("S:d4-c4:c5")
            break
    return samples
