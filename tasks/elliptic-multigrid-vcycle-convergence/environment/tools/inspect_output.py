#!/usr/bin/env python3
"""Inspect solver output for a single scenario.

Usage:
    python3 tools/inspect_output.py <label>

Reads /app/output/traces/<label>.trace and /app/output/fields/<label>.f64
and prints a small summary: residual reduction, final residual, and
solution-field peak magnitude. Provided for post-run diagnostics only —
the solver itself does not depend on this script.
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path


NX = 65
NY = 65


def load_trace(path: Path) -> list[float]:
    return [float(x) for x in path.read_text().split() if x.strip()]


def load_field(path: Path) -> tuple[float, float]:
    data = path.read_bytes()
    n = NX * NY
    expected = n * struct.calcsize("d")
    if len(data) != expected:
        raise SystemExit(f"unexpected field size: {len(data)} != {expected}")
    values = struct.unpack(f"<{n}d", data)
    peak = 0.0
    total = 0.0
    for v in values:
        if math.isnan(v) or math.isinf(v):
            raise SystemExit(f"non-finite value in {path}")
        av = abs(v)
        if av > peak:
            peak = av
        total += v * v
    rms = math.sqrt(total / n)
    return peak, rms


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    label = argv[1]
    trace = load_trace(Path(f"/app/output/traces/{label}.trace"))
    peak, rms = load_field(Path(f"/app/output/fields/{label}.f64"))
    if not trace:
        raise SystemExit(f"empty trace for {label}")
    reduction = trace[-1] / trace[0]
    print(f"scenario         : {label}")
    print(f"iterations       : {len(trace)}")
    print(f"initial residual : {trace[0]:.3e}")
    print(f"final residual   : {trace[-1]:.3e}")
    print(f"overall reduction: {reduction:.3e}")
    print(f"field peak       : {peak:.3e}")
    print(f"field rms        : {rms:.3e}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
