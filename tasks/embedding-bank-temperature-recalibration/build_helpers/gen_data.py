"""Deterministic fixture generator for embedding-bank-temperature-recalibration.

Builds the frozen banks, checkpoints, ledger, scale sheets, and the bait
surface fixture. Verifies the planted retrieval-trap geometry against every
graded corpus variant before writing anything.

Run from the task root:  python3 build_helpers/gen_data.py
"""

import json
import math
import random
import struct
from pathlib import Path

SEED = 20260725
DIM = 24
CLASSES = 6

TAU_GOOD = 0.125   # committed row for ledger line 6
TAU_BAIT_LO = 0.052
TAU_BAIT_HI = 0.066

# trap geometry
DW = 0.95           # blocker ring distance
L_RESCUE = 3.2      # rescue row weight
GAP = 0.304         # dc^2 - dw^2 ; threshold tau = GAP / L_RESCUE = 0.095
DC = math.sqrt(DW * DW + GAP)

N_TRAPS = 14        # 7 rescue-in-roster + 7 rescue-out-of-roster

ROWS_PER_SEG = 120
BLOCK = 16
COEFS = [0.5, 4.0, 0.25, 2.0]

# Per-block slot plan (16 slots each). t=recall trap (r=rescue in mix roster,
# o=rescue outside roster), n=natural, s=straddle, m=always-miss.
# Blocks 0 and 2 have sub-unit coefficients: the shipped decoder leaves those
# blocks unscaled, so their traps get shadow rings at the displaced position.
BLOCK_PLAN = [
    ["tr", "to", "tr", "to"] + ["n"] * 9 + ["s", "s", "m"],
    ["tr", "to", "to"] + ["n"] * 10 + ["s", "s", "m"],
    ["tr", "tr", "to"] + ["n"] * 10 + ["s", "s", "m"],
    ["tr", "to", "tr", "to"] + ["n"] * 9 + ["s", "s", "m"],
]
assert all(len(b) == BLOCK for b in BLOCK_PLAN)

TASK = Path(__file__).resolve().parents[1]
ENV = TASK / "environment"
DATA = ENV / "data"

PROBS_STD = [0.24, 0.21, 0.18, 0.15, 0.12, 0.10]
PROBS_B_LO = [0.34, 0.20, 0.14, 0.12, 0.11, 0.09]
PROBS_B_HI = [0.09, 0.11, 0.12, 0.14, 0.20, 0.34]

SEG_PROBS = {
    "bank_a/seg_01": PROBS_STD,
    "bank_a/seg_02": PROBS_STD,
    "bank_a/seg_03": PROBS_STD,
    "bank_a/seg_04": PROBS_STD,
    "bank_b/seg_01": PROBS_B_LO,
    "bank_b/seg_02": PROBS_B_LO,
    "bank_b/seg_03": PROBS_B_HI,
    "bank_b/seg_04": PROBS_B_HI,
}

WEFT_C = ["bank_a/seg_01", "bank_a/seg_02", "bank_b/seg_01", "bank_b/seg_02"]
WEFT_D = ["bank_a/seg_03", "bank_a/seg_04", "bank_b/seg_03", "bank_b/seg_04"]


def f32(v: float) -> float:
    return struct.unpack("<f", struct.pack("<f", v))[0]


def f32v(vec):
    return [f32(v) for v in vec]


def unit(rng):
    v = [rng.gauss(0.0, 1.0) for _ in range(DIM)]
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def add(a, b, s=1.0):
    return [a[i] + s * b[i] for i in range(DIM)]


def d2(a, b):
    s = 0.0
    for i in range(DIM):
        d = a[i] - b[i]
        s += d * d
    return s


def pick_class(rng, probs):
    r = rng.random()
    acc = 0.0
    for k, p in enumerate(probs):
        acc += p
        if r < acc:
            return k
    return len(probs) - 1


def main() -> None:
    rng = random.Random(SEED)

    # -- class centers ------------------------------------------------------
    while True:
        centers = [[2.8 * x for x in unit(rng)] for _ in range(CLASSES)]
        dmin = min(
            math.sqrt(d2(centers[i], centers[j]))
            for i in range(CLASSES)
            for j in range(i + 1, CLASSES)
        )
        if dmin >= 3.3:
            break

    # -- natural corpus rows -------------------------------------------------
    segs = {name: [] for name in SEG_PROBS}
    for name, probs in SEG_PROBS.items():
        for _ in range(ROWS_PER_SEG):
            k = pick_class(rng, probs)
            vec = f32v(add(centers[k], [rng.gauss(0.0, 0.55) for _ in range(DIM)]))
            lw = f32(rng.uniform(-0.35, 0.35))
            segs[name].append((k, lw, vec))

    natural_rows = [row[2] for rows in segs.values() for row in rows]

    # -- query slots + recall traps ------------------------------------------
    hot_points = []  # outposts and shadow-ring centers

    def clear_of_hot(p, floor2):
        return all(d2(p, h) >= floor2 for h in hot_points)

    def sample_outpost(shadow_scale):
        for _ in range(40000):
            p = [3.1 * x for x in unit(rng)]
            if min(d2(p, c) for c in centers) < 1.8 * 1.8:
                continue
            if not clear_of_hot(p, 12.25):
                continue
            if min(d2(p, r) for r in natural_rows) < 2.89:
                continue
            if shadow_scale is not None:
                sp = [shadow_scale * x for x in p]
                if not clear_of_hot(sp, 9.0):
                    continue
                if min(d2(sp, r) for r in natural_rows) < 2.89:
                    continue
                hot_points.append(sp)
            hot_points.append(p)
            return p
        raise SystemExit("could not place outpost")

    trap_meta = []
    queries = {}

    for fam, pair in (("a", (0, 5)), ("b", (0, 2))):
        if fam == "a":
            blocker_segs = ["bank_a/seg_01", "bank_a/seg_02"]
            shadow_segs = ["bank_a/seg_01", "bank_a/seg_02"]
            rescue_in = "bank_a/seg_02"
            rescue_out = "bank_a/seg_03"
        else:
            blocker_segs = ["bank_b/seg_03", "bank_b/seg_04"]
            shadow_segs = ["bank_b/seg_03", "bank_b/seg_04"]
            rescue_in = "bank_b/seg_04"
            rescue_out = "bank_b/seg_02"
        fam_queries = []
        t = 0
        for bi, plan in enumerate(BLOCK_PLAN):
            coef = COEFS[bi]
            shadow_scale = (1.0 / coef) if coef < 1.0 else None
            for kind in plan:
                if kind in ("tr", "to"):
                    qc = t % CLASSES
                    p = sample_outpost(shadow_scale)
                    q = f32v(p)
                    for j in range(10):
                        bc = (qc + 1 + (j % (CLASSES - 1))) % CLASSES
                        bvec = f32v(add(p, unit(rng), DW))
                        blw = f32(rng.uniform(-0.05, 0.0))
                        segs[blocker_segs[j % 2]].append((bc, blw, bvec))
                    rseg = rescue_in if kind == "tr" else rescue_out
                    rvec = f32v(add(p, unit(rng), DC))
                    segs[rseg].append((qc, f32(L_RESCUE), rvec))
                    if shadow_scale is not None:
                        sp = [shadow_scale * x for x in p]
                        for j in range(10):
                            sc = (qc + 1 + (j % (CLASSES - 1))) % CLASSES
                            svec = f32v(add(sp, unit(rng), 0.8))
                            slw = f32(rng.uniform(-0.05, 0.0))
                            segs[shadow_segs[j % 2]].append((sc, slw, svec))
                    trap_meta.append((fam, t, qc, q, rseg, shadow_scale))
                    fam_queries.append((qc, q))
                    t += 1
                elif kind == "n":
                    k = len(fam_queries) % CLASSES
                    noise = [rng.gauss(0.0, 0.6) for _ in range(DIM)]
                    fam_queries.append((k, f32v(add(centers[k], noise))))
                elif kind == "s":
                    i, j = pair
                    mid = [(centers[i][d] + centers[j][d]) / 2.0 for d in range(DIM)]
                    fam_queries.append(
                        (i, f32v(add(mid, [rng.gauss(0.0, 0.30) for _ in range(DIM)])))
                    )
                else:  # always-miss
                    k = len(fam_queries) % CLASSES
                    wrong = (k + 3) % CLASSES
                    noise = [rng.gauss(0.0, 0.30) for _ in range(DIM)]
                    fam_queries.append((k, f32v(add(centers[wrong], noise))))
        assert t == N_TRAPS
        assert len(fam_queries) == 4 * BLOCK
        queries[fam] = fam_queries

    # -- verification against every graded corpus variant --------------------
    def corpus(names):
        rows = []
        for n in names:
            rows.extend(segs[n])
        return rows

    fam_a = corpus(["bank_a/seg_01", "bank_a/seg_02", "bank_a/seg_03", "bank_a/seg_04"])
    fam_b = corpus(["bank_b/seg_01", "bank_b/seg_02", "bank_b/seg_03", "bank_b/seg_04"])
    mix_c = corpus(WEFT_C)
    mix_d = corpus(WEFT_D)
    full8 = fam_a + fam_b

    def hit(q, qc, rows, tau):
        scored = sorted(
            ((-d2(q, r[2]) + tau * r[1], i) for i, r in enumerate(rows)),
            key=lambda x: (-x[0], x[1]),
        )
        return any(rows[i][0] == qc for _, i in scored[:10])

    variants = {
        "fam_a": fam_a,
        "fam_b": fam_b,
        "mix_c": mix_c,
        "mix_d": mix_d,
        "full8": full8,
    }
    all_taus = (TAU_GOOD, TAU_BAIT_LO, TAU_BAIT_HI, 0.064, 0.058, 0.0)
    for fam, t, qc, q, rseg, shadow_scale in trap_meta:
        fam_rows = variants["fam_a" if fam == "a" else "fam_b"]
        assert hit(q, qc, fam_rows, TAU_GOOD), f"trap {fam}{t}: family hit at good tau"
        for bait in (TAU_BAIT_LO, TAU_BAIT_HI, 0.064, 0.058, 0.0):
            assert not hit(q, qc, fam_rows, bait), f"trap {fam}{t}: miss at bait tau"
        mrows = variants["mix_c" if fam == "a" else "mix_d"]
        roster = WEFT_C if fam == "a" else WEFT_D
        if rseg in roster:
            assert hit(q, qc, mrows, TAU_GOOD), f"trap {fam}{t}: roster hit"
        else:
            assert not hit(q, qc, mrows, TAU_GOOD), f"trap {fam}{t}: roster miss"
            assert hit(q, qc, full8, TAU_GOOD), f"trap {fam}{t}: full-corpus hit"
        if shadow_scale is not None:
            sq = [shadow_scale * x for x in q]
            for rows_name in ("fam_a" if fam == "a" else "fam_b",
                              "mix_c" if fam == "a" else "mix_d",
                              "full8"):
                for tau in all_taus:
                    assert not hit(sq, qc, variants[rows_name], tau), (
                        f"trap {fam}{t}: displaced miss in {rows_name} at tau={tau}"
                    )

    for fam in ("a", "b"):
        fam_rows = variants[f"fam_{fam}"]
        mrows = variants["mix_c" if fam == "a" else "mix_d"]
        for slot, (qc, q) in enumerate(queries[fam]):
            kind = BLOCK_PLAN[slot // BLOCK][slot % BLOCK]
            if kind == "m":
                for rows in (fam_rows, mrows, full8):
                    for tau in all_taus:
                        assert not hit(q, qc, rows, tau), f"always-miss {fam}{slot} hit"

    # -- write banks ----------------------------------------------------------
    for name, rows in segs.items():
        path = DATA / "banks" / Path(name + ".bin")
        path.parent.mkdir(parents=True, exist_ok=True)
        buf = bytearray()
        buf += b"SGB1"
        buf += struct.pack("<II", len(rows), DIM)
        for k, lw, vec in rows:
            buf += struct.pack("<H", k)
            buf += struct.pack("<f", lw)
            buf += struct.pack(f"<{DIM}f", *vec)
        path.write_bytes(bytes(buf))

    # -- write checkpoints ----------------------------------------------------
    ck = DATA / "checkpoints"
    ck.mkdir(parents=True, exist_ok=True)
    for fam in ("a", "b"):
        rows = queries[fam]
        cold = bytearray()
        cold += b"CKP1"
        cold += struct.pack("<II", len(rows), DIM)
        for k, _ in rows:
            cold += struct.pack("<H", k)
        for _, vec in rows:
            cold += struct.pack(f"<{DIM}f", *vec)
        (ck / f"cold_{fam}.ckpt").write_bytes(bytes(cold))

        warm = bytearray()
        warm += b"CKP2"
        warm += struct.pack("<III", len(rows), DIM, BLOCK)
        for k, _ in rows:
            warm += struct.pack("<H", k)
        for bi in range(0, len(rows), BLOCK):
            coef = COEFS[(bi // BLOCK) % len(COEFS)]
            warm += struct.pack("<f", coef)
            for _, vec in rows[bi : bi + BLOCK]:
                for v in vec:
                    m = v / coef
                    assert f32(m) * coef == v, "mantissa roundtrip must be exact"
                    warm += struct.pack("<f", m)
        (ck / f"resume_{fam}.ckpt").write_bytes(bytes(warm))

    # -- ledger ----------------------------------------------------------------
    led = DATA / "ledger"
    led.mkdir(parents=True, exist_ok=True)
    marks = [
        {
            "idx": 3,
            "state": "commit",
            "sheet": "a7",
            "weft_c": ["bank_a/seg_01", "bank_a/seg_03",
                       "bank_b/seg_02", "bank_b/seg_04"],
            "weft_d": ["bank_a/seg_02", "bank_a/seg_04",
                       "bank_b/seg_01", "bank_b/seg_03"],
            "note": "quarterly refresh",
        },
        {
            "idx": 4,
            "state": "commit",
            "sheet": "a7",
            "weft_c": ["bank_a/seg_02", "bank_a/seg_03",
                       "bank_b/seg_01", "bank_b/seg_04"],
            "weft_d": ["bank_a/seg_01", "bank_a/seg_04",
                       "bank_b/seg_02", "bank_b/seg_03"],
            "note": "post-ingest rebalance",
        },
        {"idx": 5, "state": "draft", "sheet": "w2", "note": "sweep prep"},
        {
            "idx": 6,
            "state": "commit",
            "sheet": "a7",
            "weft_c": WEFT_C,
            "weft_d": WEFT_D,
            "note": "composition refresh",
        },
        {"idx": 7, "state": "draft", "sheet": "w2", "note": "recal sweep pass one"},
        {"idx": 8, "state": "draft", "sheet": "w2", "note": "recal sweep pass two"},
    ]
    with open(led / "journal.jsonl", "w", encoding="utf-8") as fh:
        for m in marks:
            fh.write(json.dumps(m, separators=(",", ":")) + "\n")

    # -- scale sheets ------------------------------------------------------------
    sched = DATA / "sched"
    sched.mkdir(parents=True, exist_ok=True)
    (sched / "table_a7.toml").write_text(
        "# Committed scale rows by ledger line.\n"
        "[rows]\n"
        '"3" = 0.121000\n'
        '"4" = 0.123000\n'
        '"6" = 0.125000\n',
        encoding="utf-8",
    )
    (sched / "table_w2.toml").write_text(
        "# Working sweep scale rows by ledger line.\n"
        "[rows]\n"
        '"3" = 0.049000\n'
        '"4" = 0.052000\n'
        '"5" = 0.055000\n'
        '"6" = 0.058000\n'
        '"7" = 0.061000\n'
        '"8" = 0.064000\n',
        encoding="utf-8",
    )

    # -- bait surface fixture ------------------------------------------------------
    fx = DATA / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    bait_cells = []
    bait_vals = {
        "cold_a": (0.929600, 0.543900),
        "resume_a": (0.929600, 0.543900),
        "cold_b": (0.924100, 0.502800),
        "resume_b": (0.924100, 0.502800),
        "mix_c": (0.832900, 0.526100),
        "mix_d": (0.846400, 0.491700),
    }
    for cid, (r, n) in bait_vals.items():
        bait_cells.append(
            {
                "id": cid,
                "recall_at_10": r,
                "nmi": n,
                "temperature": 0.125000,
                "bank_epoch": 6,
            }
        )
    surface = {
        "schema_tag": "embed-eval-v2",
        "source": "surfscan-dash",
        "swept": "rotation-w29",
        "scenarios": bait_cells,
        "bands_ok": True,
    }
    (fx / "surface_ok.json").write_text(
        json.dumps(surface, indent=2) + "\n", encoding="utf-8"
    )

    n_rows = {k: len(v) for k, v in segs.items()}
    print("segment rows:", n_rows)
    print("queries per family:", {k: len(v) for k, v in queries.items()})
    print("trap geometry verified against fam_a fam_b mix_c mix_d full8")


if __name__ == "__main__":
    main()
