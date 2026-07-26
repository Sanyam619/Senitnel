"""Reference pipeline for int4-weight-only-calibration-eval.

Pure stdlib, and every loop is written in the order the Rust engine walks it so
the two agree to the last bits of a double.
"""

from __future__ import annotations

import math
import random

# ------------------------------------------------------------------ geometry
WIDTH = 32
DIMS = [(24, 32), (16, 24), (16, 16)]  # (out, in) per hidden layer
CLASSES = 8
TAIL = DIMS[-1][0]
EPS = 1e-6

# Every quantized linear layer, widest first: three hidden layers then the head.
IN_DIMS = [32, 24, 16, 16]
OUT_DIMS = [24, 16, 16, 8]

DOMAINS = {"a": (0.25, 1.05), "b": (-0.20, 0.95)}

CALIB_N = {"a": 64, "b": 64, "c": 48, "d": 56}
EVAL_N = 160
MARGIN_FLOOR = 2e-3

# epoch, state, kind, group width
TIPS = {
    "tip_g2": (2, "staged", "grouped", 2),
    "tip_g4": (4, "sealed", "grouped", 4),
    "tip_g5": (5, "staged", "grouped", 8),
    "tip_g6": (6, "sealed", "grouped", 4),
    "tip_g7": (7, "sealed", "grouped", 8),
    "tip_g9": (9, "sealed", "grouped", 4),
    "tip_g11": (11, "sealed", "per_channel", 32),
    "tip_live": (12, "live", "per_channel", 32),
}
RETIRED = ["tip_g9"]
BOUND = "tip_g7"

# shard -> (first epoch admitted, last epoch admitted)
ADMIT = {
    "shard_a": (3, 20),
    "shard_b": (5, 20),
    "shard_c": (1, 6),
    "shard_d": (9, 20),
}


def relu(v):
    return 0.0 if v < 0.0 else v


def nearest(v):
    """Half away from zero, matching Rust's f64::round."""
    return math.floor(v + 0.5) if v >= 0.0 else math.ceil(v - 0.5)


def sample_rows(rng, n, shift, scale, width=WIDTH):
    return [[shift + scale * rng.gauss(0.0, 1.0) for _ in range(width)] for _ in range(n)]


def mixed_rows(rng, n, lead="a"):
    other = "b" if lead == "a" else "a"
    rows = []
    for k in range(n):
        shift, scale = DOMAINS[lead if k % 2 == 0 else other]
        rows.append([shift + scale * rng.gauss(0.0, 1.0) for _ in range(WIDTH)])
    return rows


# ------------------------------------------------------------------- weights
SHARP = 2.9
OUTLIER_RATE = 0.07
OUTLIER_GAIN = 5.5


def _spike(rng, mat):
    for row in mat:
        for i in range(len(row)):
            if rng.random() < OUTLIER_RATE:
                row[i] *= OUTLIER_GAIN


def build_fp16(seed=20260726):
    rng = random.Random(seed)
    w = []
    b = []
    for out, inn in DIMS:
        mat = [[rng.gauss(0.0, 1.0 / math.sqrt(inn)) for _ in range(inn)] for _ in range(out)]
        _spike(rng, mat)
        w.append(mat)
        b.append([rng.gauss(0.0, 0.10) for _ in range(out)])
    head_w = [
        [rng.gauss(0.0, SHARP / math.sqrt(TAIL)) for _ in range(TAIL)] for _ in range(CLASSES)
    ]
    _spike(rng, head_w)
    head_b = [rng.gauss(0.0, 0.20 * SHARP) for _ in range(CLASSES)]
    return {"w": w + [head_w], "b": b + [head_b]}


def layers(ck):
    """(weights, bias) of every quantized linear layer, in forward order."""
    return list(zip(ck["w"], ck["b"]))


def forward(ck, row):
    """Class responses of one input row, and the input each layer saw."""
    seen = []
    cur = row
    for at, (w, b) in enumerate(layers(ck)):
        seen.append(cur)
        nxt = []
        for o in range(len(w)):
            acc = b[o]
            wo = w[o]
            for i in range(len(cur)):
                acc += wo[i] * cur[i]
            nxt.append(acc if at == len(DIMS) else relu(acc))
        cur = nxt
    return cur, seen


def logits_of(ck, rows):
    return [forward(ck, r)[0] for r in rows]


def argmax_margin(vals):
    best = 0
    for c in range(1, len(vals)):
        if vals[c] > vals[best]:
            best = c
    order = sorted(vals, reverse=True)
    return best, order[0] - order[1]


def labels_of(ck, rows):
    out = []
    gaps = []
    for row in rows:
        best, gap = argmax_margin(forward(ck, row)[0])
        out.append(best)
        gaps.append(gap)
    return out, gaps


# -------------------------------------------------------- activation scaling
def fit_gains(ck, rows):
    """Per-input-channel gains measured over the calibration rows."""
    total = [[0.0] * d for d in IN_DIMS]
    for row in rows:
        _, seen = forward(ck, row)
        for at, vec in enumerate(seen):
            acc = total[at]
            for i in range(len(vec)):
                acc[i] += abs(vec[i])
    n = float(len(rows))
    out = []
    for at, d in enumerate(IN_DIMS):
        g = [math.sqrt(total[at][i] / n + EPS) for i in range(d)]
        s = 0.0
        for v in g:
            s += v
        mid = s / float(d)
        out.append([v / mid for v in g])
    return out


def span_of(group, in_dim):
    if group == 0 or group > in_dim or in_dim % group != 0:
        return in_dim
    return group


def grid_span(group):
    return sum(IN_DIMS[at] // span_of(group, IN_DIMS[at]) for at in range(len(IN_DIMS)))


def pack(w, gains, group):
    """INT4 weight-only round trip of one layer, grouped over input channels."""
    rows = len(w)
    in_dim = len(w[0])
    ext = span_of(group, in_dim)
    out = [[0.0] * in_dim for _ in range(rows)]
    for o in range(rows):
        for head in range(0, in_dim, ext):
            top = 0.0
            for i in range(head, head + ext):
                v = abs(w[o][i] * gains[i])
                if v > top:
                    top = v
            step = top / 7.0 if top > 0.0 else 1.0
            for i in range(head, head + ext):
                q = nearest(w[o][i] * gains[i] / step)
                if q > 7.0:
                    q = 7.0
                if q < -8.0:
                    q = -8.0
                out[o][i] = q * step / gains[i]
    return out


def pack_rowwise(w, gains, group):
    """The engine's shipped reduction: group extent walks the output rows."""
    rows = len(w)
    in_dim = len(w[0])
    ext = span_of(group, rows)
    out = [[0.0] * in_dim for _ in range(rows)]
    for i in range(in_dim):
        for head in range(0, rows, ext):
            top = 0.0
            for o in range(head, head + ext):
                v = abs(w[o][i] * gains[i])
                if v > top:
                    top = v
            step = top / 7.0 if top > 0.0 else 1.0
            for o in range(head, head + ext):
                q = nearest(w[o][i] * gains[i] / step)
                if q > 7.0:
                    q = 7.0
                if q < -8.0:
                    q = -8.0
                out[o][i] = q * step / gains[i]
    return out


def quantized(ck, gains, group, packer=pack):
    return {
        "w": [packer(w, gains[at], group) for at, (w, _) in enumerate(layers(ck))],
        "b": ck["b"],
    }


# -------------------------------------------------------------------- scoring
def measure(ck, rows, marks):
    total = 0.0
    hit = 0
    for at, row in enumerate(rows):
        vals = forward(ck, row)[0]
        top = vals[0]
        best = 0
        for c in range(1, CLASSES):
            if vals[c] > top:
                top = vals[c]
                best = c
        acc = 0.0
        for c in range(CLASSES):
            acc += math.exp(vals[c] - top)
        total += top + math.log(acc) - vals[marks[at]]
        if best == marks[at]:
            hit += 1
    n = float(len(rows))
    return math.exp(total / n), float(hit) / n


# ----------------------------------------------------------------- admission
def admitted(epoch):
    return [s for s in sorted(ADMIT) if ADMIT[s][0] <= epoch <= ADMIT[s][1]]


def resolve():
    best = None
    for tip, (epoch, state, kind, _) in TIPS.items():
        if state != "sealed" or tip in RETIRED or kind != "grouped":
            continue
        if best is None or epoch > TIPS[best][0]:
            best = tip
    return best
