#!/usr/bin/env python3
"""Fixture generator for the ASR evaluation desk.

Writes frozen frame posteriors, reference alignments, the lexicon, the bigram
fusion table, the prediction-state bias table, per-sheet fusion rows, the
decoder tip journal, and the surface artifacts under environment/data/.

It also reports the metrics a faithful engine produces for each decode variant
so the published bands can be chosen with real separation between the bound
configuration and the near-miss configurations.
"""

from __future__ import annotations

import json
import math
import random
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "environment"
DATA = ROOT / "data"

WORDS = [
    "<b>",
    "the",
    "cat",
    "sat",
    "on",
    "mat",
    "dog",
    "ran",
    "far",
    "red",
    "car",
    "top",
    "hat",
    "map",
]
V = len(WORDS)

# acoustically confusable partners (symmetric)
CONF = {
    1: 4,
    4: 1,
    2: 12,
    12: 2,
    3: 11,
    11: 3,
    5: 13,
    13: 5,
    6: 7,
    7: 6,
    8: 10,
    10: 8,
}

# successor preferences drive an informative bigram table
GRAMMAR = {
    0: [1, 1, 1, 2, 6, 10],
    1: [2, 6, 5, 10, 12, 9, 11],
    2: [3, 7, 4, 3],
    3: [4, 4, 1],
    4: [1, 1, 5, 12],
    5: [1, 4, 3],
    6: [7, 3, 4, 7],
    7: [8, 4, 1, 8],
    8: [1, 4, 9],
    9: [10, 2, 5],
    10: [7, 8, 4],
    11: [4, 1, 5],
    12: [4, 1, 3],
    13: [4, 1, 9],
}

SLICES = ["read_a", "read_b", "spont_a", "spont_b", "far_c", "far_d"]
UTTS = 6

# per-slice span mix: (irreducible, fusion-restorable, over-fusion trap,
# neighbouring-row sensitive)
PROFILE = {
    "read_a": (0.12, 0.26, 0.24, 0.22),
    "read_b": (0.09, 0.26, 0.24, 0.22),
    "spont_a": (0.16, 0.26, 0.24, 0.22),
    "spont_b": (0.20, 0.34, 0.24, 0.22),
    "far_c": (0.44, 0.26, 0.24, 0.22),
    "far_d": (0.46, 0.26, 0.24, 0.22),
}

SEEDS = {
    "read_a": 91117,
    "read_b": 91223,
    "spont_a": 91331,
    "spont_b": 91447,
    "far_c": 91559,
    "far_d": 91661,
}

BOUND_W = 0.35
PLAIN_W = 0.0
OTHER_W = 0.62
NOVEL_W = 0.30


def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def build_corpus(n: int) -> list[list[int]]:
    rng = random.Random(20260725)
    out = []
    for _ in range(n):
        length = rng.randint(7, 14)
        cur = 0
        sent = []
        for _ in range(length):
            nxt = rng.choice(GRAMMAR[cur])
            sent.append(nxt)
            cur = nxt
        out.append(sent)
    return out


def build_lm(corpus: list[list[int]]) -> list[list[float]]:
    counts = [[0.30 for _ in range(V)] for _ in range(V)]
    for sent in corpus:
        prev = 0
        for tok in sent:
            counts[prev][tok] += 1.0
            prev = tok
    lm = [[0.0 for _ in range(V)] for _ in range(V)]
    for p in range(V):
        total = sum(counts[p][1:])
        for v in range(1, V):
            lm[p][v] = f32(math.log(counts[p][v] / total))
        lm[p][0] = f32(-12.0)
    return lm


def build_bias(lm: list[list[float]]) -> list[list[float]]:
    bias = [[0.0 for _ in range(V)] for _ in range(V)]
    rng = random.Random(4242)
    for p in range(V):
        for v in range(V):
            jitter = (rng.random() - 0.5) * 0.12
            bias[p][v] = f32(0.45 * lm[p][v] + jitter)
        bias[p][0] = f32(0.0)
    return bias


def build_refs(slice_id: str) -> list[list[int]]:
    rng = random.Random(SEEDS[slice_id])
    utts = []
    for _ in range(UTTS):
        length = rng.randint(9, 14)
        cur = 0
        sent: list[int] = []
        while len(sent) < length:
            nxt = rng.choice(GRAMMAR[cur])
            # a fraction of the transcripts hold the acoustically close
            # neighbour of the expected successor, so the fusion prior points
            # away from what was actually spoken
            if rng.random() < 0.24:
                nxt = CONF.get(nxt, nxt)
            sent.append(nxt)
            cur = nxt
            if sent and rng.random() < 0.17:
                sent.append(nxt)
        utts.append(sent[:length])
    return utts


def span_plan(slice_id: str, ref: list[int], lm: list[list[float]]) -> list[dict]:
    """Assign an acoustic gap to every reference token span.

    A span whose gap depends on the fusion weight is only placed after a span
    that decodes cleanly, so the conditioning context at that point is the
    reference context and the intended separation holds exactly.
    """
    rng = random.Random(SEEDS[slice_id] * 7 + len(ref))
    p_err, p_res, p_trap, p_edge = PROFILE[slice_id]
    plan = []
    prev = 0
    prev_tok = -1
    prev_clean = True
    for tok in ref:
        cands = [c for c in (CONF.get(tok), tok - 1, tok + 1) if c and 1 <= c < V and c != tok]
        repeat = tok == prev_tok
        kind = "clean"
        d = 0.0
        partner = CONF.get(tok)
        if cands and not repeat and prev_clean:
            deltas = {c: lm[prev][tok] - lm[prev][c] for c in cands}
            up = [c for c in cands if 0.25 < deltas[c] < 6.0]
            down = [c for c in cands if -6.0 < deltas[c] < -0.25]
            near = [c for c in cands if abs(deltas[c]) < 2.5]
            roll = rng.random()
            if roll < p_err and near:
                pick = partner if partner in near else near[0]
                kind, partner, d = "err", pick, deltas[pick]
            elif roll < p_err + p_res and up:
                pick = max(up, key=lambda c: deltas[c])
                kind, partner, d = "res", pick, deltas[pick]
            elif roll < p_err + p_res + p_trap and down:
                pick = min(down, key=lambda c: deltas[c])
                kind, partner, d = "trap", pick, deltas[pick]
            elif roll < p_err + p_res + p_trap + p_edge and up:
                pick = max(up, key=lambda c: deltas[c])
                kind, partner, d = "edge", pick, deltas[pick]
                edge_f = 0.245 if rng.random() < 0.5 else 0.315
        if kind == "err":
            gap = -0.62 * max(d, 0.0) - 0.40
            dur = 1
        elif kind == "res":
            gap = -0.175 * d
            dur = 1
        elif kind == "trap":
            gap = 0.45 * (-d)
            dur = 1
        elif kind == "edge":
            gap = -edge_f * d
            dur = 1
        else:
            if partner is None:
                partner = cands[0] if cands else 0
            spread = 0.0
            if partner:
                spread = max(abs(lm[p][tok] - lm[p][partner]) for p in range(V))
            gap = min(5.5, 0.75 * spread + 0.8)
            dur = rng.randint(1, 3)
        plan.append(
            {
                "tok": tok,
                "partner": partner if partner is not None else 0,
                "gap": gap,
                "dur": dur,
                "gapfill": 2 if repeat else rng.randint(1, 2),
                "kind": kind,
            }
        )
        prev = tok
        prev_tok = tok
        prev_clean = kind == "clean"
    return plan


def frames_for(plan: list[dict]) -> list[list[float]]:
    frames: list[list[float]] = []
    for span in plan:
        tok = span["tok"]
        partner = span["partner"]
        for _ in range(span["dur"]):
            row = [f32(-6.0)] * V
            row[0] = f32(-5.0)
            row[tok] = f32(-0.10)
            if partner:
                row[partner] = f32(-0.10 - span["gap"])
            frames.append(row)
        for _ in range(span["gapfill"]):
            row = [f32(-7.0)] * V
            row[0] = f32(-0.05)
            frames.append(row)
    return frames


def write_frames(path: Path, frames: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = bytearray()
    blob += b"APF1"
    blob += struct.pack("<I", len(frames))
    blob += struct.pack("<I", V)
    for row in frames:
        for val in row:
            blob += struct.pack("<f", val)
    path.write_bytes(bytes(blob))


def write_table(path: Path, magic: bytes, table: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = bytearray()
    blob += magic
    blob += struct.pack("<I", V)
    for row in table:
        for val in row:
            blob += struct.pack("<f", val)
    path.write_bytes(bytes(blob))


def decode_collapse(frames, lm, w, ordered=True):
    """Greedy frame decode. ordered=True collapses repeats before dropping the
    blank label; ordered=False drops blanks first."""
    raw = []
    last = 0
    for row in frames:
        best = 0
        best_s = None
        for v in range(V):
            s = row[v]
            if v != 0:
                s += w * lm[last][v]
            if best_s is None or s > best_s:
                best_s = s
                best = v
        raw.append(best)
        if best != 0:
            last = best
    out = []
    if ordered:
        prev = -1
        for lab in raw:
            if lab != prev and lab != 0:
                out.append(lab)
            prev = lab
    else:
        prev = -1
        for lab in raw:
            if lab == 0:
                continue
            if lab != prev:
                out.append(lab)
            prev = lab
    return out


def decode_join(frames, lm, bias, w, stateful=True):
    if not stateful:
        return decode_collapse(frames, lm, w, True)
    out: list[int] = []
    last = 0
    t = 0
    while t < len(frames):
        row = frames[t]
        emitted = 0
        while True:
            best = 0
            best_s = None
            for v in range(V):
                s = row[v]
                if v != 0:
                    s += w * lm[last][v]
                    if stateful:
                        s += bias[last][v]
                if best_s is None or s > best_s:
                    best_s = s
                    best = v
            if best == 0 or emitted >= 2:
                t += 1
                break
            out.append(best)
            last = best
            emitted += 1
    return out


def edit(a: list, b: list) -> int:
    prev = list(range(len(b) + 1))
    for i, ai in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, bj in enumerate(b, 1):
            cur[j] = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (0 if ai == bj else 1),
            )
        prev = cur
    return prev[-1]


def score(hyps, refs):
    we = wn = ce = cn = 0
    for hyp, ref in zip(hyps, refs):
        hw = [WORDS[i] for i in hyp]
        rw = [WORDS[i] for i in ref]
        we += edit(hw, rw)
        wn += len(rw)
        ce += edit(list(" ".join(hw)), list(" ".join(rw)))
        cn += len(" ".join(rw))
    return we / wn, ce / cn


def main() -> None:
    corpus = build_corpus(600)
    lm = build_lm(corpus)
    bias = build_bias(lm)

    (DATA / "lexicon").mkdir(parents=True, exist_ok=True)
    (DATA / "lexicon" / "tokens.txt").write_text(
        "\n".join(f"{i} {w}" for i, w in enumerate(WORDS)) + "\n", encoding="utf-8"
    )
    write_table(DATA / "lm" / "bigram.bin", b"LMB1", lm)
    write_table(DATA / "predict" / "bias.bin", b"PRD1", bias)

    variants = {
        "bound_ctc": [],
        "plain_ctc": [],
        "other_ctc": [],
        "unordered_ctc": [],
        "novel_rnnt": [],
        "flat_rnnt": [],
    }
    for sid in SLICES:
        refs = build_refs(sid)
        lines = []
        allframes = []
        for i, ref in enumerate(refs, 1):
            plan = span_plan(sid, ref, lm)
            frames = frames_for(plan)
            allframes.append(frames)
            write_frames(DATA / "audio" / sid / f"utt_{i:02d}.bin", frames)
            lines.append(f"utt_{i:02d}\t" + " ".join(WORDS[t] for t in ref))
        (DATA / "align").mkdir(parents=True, exist_ok=True)
        (DATA / "align" / f"{sid}.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

        def run(fn, allframes=allframes, refs=refs):
            return score([fn(f) for f in allframes], refs)

        variants["bound_ctc"].append(
            (sid, run(lambda f: decode_collapse(f, lm, BOUND_W, True)))
        )
        variants["plain_ctc"].append(
            (sid, run(lambda f: decode_collapse(f, lm, PLAIN_W, True)))
        )
        variants["other_ctc"].append(
            (sid, run(lambda f: decode_collapse(f, lm, OTHER_W, True)))
        )
        variants["unordered_ctc"].append(
            (sid, run(lambda f: decode_collapse(f, lm, BOUND_W, False)))
        )
        variants["novel_rnnt"].append(
            (sid, run(lambda f: decode_join(f, lm, bias, NOVEL_W, True)))
        )
        variants["flat_rnnt"].append(
            (sid, run(lambda f: decode_join(f, lm, bias, NOVEL_W, False)))
        )

    for name, rows in variants.items():
        print(f"--- {name}")
        for sid, (wer, cer) in rows:
            print(f"  {sid:9s} wer={wer:.6f} cer={cer:.6f}")

    bands = {}
    for sid, (wer, cer) in variants["bound_ctc"]:
        bands[sid] = (
            round(max(0.0, wer - 0.020), 3),
            round(wer + 0.020, 3),
            round(max(0.0, cer - 0.016), 3),
            round(cer + 0.016, 3),
        )
    print("--- proposed bands")
    for sid in SLICES:
        print(f"  {sid} {bands[sid]}")

    conflicts = []
    for name in ("plain_ctc", "other_ctc", "unordered_ctc"):
        for sid, (wer, cer) in variants[name]:
            lo_w, hi_w, lo_c, hi_c = bands[sid]
            inside = lo_w <= wer <= hi_w and lo_c <= cer <= hi_c
            if inside:
                conflicts.append((name, sid, wer, cer))
    print("--- near-miss variants landing inside bands:", conflicts or "none")

    journal = [
        {"idx": 2, "state": "sealed", "tip": "tip_b2", "sheet": "h4", "mode": "ctc_collapse"},
        {"idx": 3, "state": "live", "tip": "tip_c3", "sheet": "k9", "mode": "rnnt_join"},
        {"idx": 5, "state": "sealed", "tip": "tip_e5", "sheet": "h4", "mode": "ctc_collapse"},
        {"idx": 7, "state": "live", "tip": "tip_g7", "sheet": "k9", "mode": "rnnt_join"},
        {"idx": 6, "state": "sealed", "tip": "tip_f6", "sheet": "h4", "mode": "ctc_collapse"},
        {"idx": 9, "state": "sealed", "tip": "tip_j9", "sheet": "k9", "mode": "rnnt_join"},
        {"idx": 11, "state": "live", "tip": "tip_m11", "sheet": "k9", "mode": "rnnt_join"},
    ]
    (DATA / "decoder_registry").mkdir(parents=True, exist_ok=True)
    (DATA / "decoder_registry" / "tip_journal.jsonl").write_text(
        "\n".join(json.dumps(r) for r in journal) + "\n", encoding="utf-8"
    )
    (DATA / "decoder_registry" / "retired_tips.jsonl").write_text(
        json.dumps({"tip": "tip_j9", "at": "2026-06-30T09:14:00Z", "by": "eval-rotation"})
        + "\n",
        encoding="utf-8",
    )

    (DATA / "fusion").mkdir(parents=True, exist_ok=True)
    (DATA / "fusion" / "table_h4.toml").write_text(
        "# shallow-fusion rows measured on sheet h4\n"
        '"2" = 0.220000\n'
        '"5" = 0.280000\n'
        f'"6" = {BOUND_W:.6f}\n'
        '"8" = 0.710000\n',
        encoding="utf-8",
    )
    (DATA / "fusion" / "table_k9.toml").write_text(
        "# shallow-fusion rows measured on sheet k9\n"
        '"3" = 0.540000\n'
        '"7" = 0.600000\n'
        '"9" = 0.580000\n'
        f'"11" = {OTHER_W:.6f}\n'
        '"13" = 0.440000\n',
        encoding="utf-8",
    )

    sweep = {
        "captured": "2026-07-04T02:11:00Z",
        "view": "surface sweep dashboard",
        "slices": [
            {
                "id": sid,
                "wer": round(wer + 0.006, 6),
                "cer": round(cer + 0.005, 6),
            }
            for sid, (wer, cer) in variants["bound_ctc"]
        ],
    }
    (DATA / "fixtures").mkdir(parents=True, exist_ok=True)
    (DATA / "fixtures" / "probe_ok.json").write_text(
        json.dumps(sweep, indent=2) + "\n", encoding="utf-8"
    )

    legacy = [
        {"run": "2026-06-11", "sheet": "k9", "note": "pre-freeze sweep", "wer": 0.244},
        {"run": "2026-06-18", "sheet": "k9", "note": "pre-freeze sweep", "wer": 0.231},
        {"run": "2026-06-25", "sheet": "h4", "note": "pre-freeze sweep", "wer": 0.198},
    ]
    (DATA / "sweep").mkdir(parents=True, exist_ok=True)
    (DATA / "sweep" / "legacy_runs.jsonl").write_text(
        "\n".join(json.dumps(r) for r in legacy) + "\n", encoding="utf-8"
    )

    print("--- wrote fixtures under", DATA)


if __name__ == "__main__":
    main()
