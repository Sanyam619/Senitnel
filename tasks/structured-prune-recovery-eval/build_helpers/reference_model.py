"""Reference pipeline + fixture generator for structured-prune-recovery-eval.

Pure stdlib so the loop order matches the Rust engine exactly.
"""

from __future__ import annotations

import math
import random

# ---------------------------------------------------------------- architecture
DIMS = [(16, 12), (16, 16), (12, 16)]  # (out, in) per hidden layer
SPATIAL = [64, 32, 16]
CORE = [10, 11, 8]                     # channels that carry the decision
CLASSES = 5
EPS = 1e-5
IN_DIM = 12

MASK_TIPS = {
    "tip_g2": (2, [9, 10, 7]),
    "tip_g5": (5, [11, 12, 9]),
    "tip_g7": (7, [10, 11, 8]),
    "tip_g9": (9, [12, 12, 10]),
    "tip_live": (11, [13, 14, 11]),
}

DOMAINS = {"a": (0.26, 1.10), "b": (-0.22, 0.90)}

EVAL_N = 200
CALIB_N = 96
REF_N = 512
MARGIN_FLOOR = 5e-3


def relu(v):
    return max(0.0, v)


def sample_rows(rng, n, shift, scale, width=IN_DIM):
    return [[shift + scale * rng.gauss(0.0, 1.0) for _ in range(width)] for _ in range(n)]


def mixed_rows(rng, n):
    rows = []
    for k in range(n):
        shift, scale = DOMAINS["a" if k % 2 == 0 else "b"]
        rows.append([shift + scale * rng.gauss(0.0, 1.0) for _ in range(IN_DIM)])
    return rows


def rank_order(seed, dim):
    """Channel order from most to least important."""
    order = list(range(dim))
    random.Random(seed).shuffle(order)
    return order


def build_dense(seed=20260725):
    rng = random.Random(seed)
    order = [rank_order(500 + k, DIMS[k][0]) for k in range(len(DIMS))]
    rank = []
    for k in range(len(DIMS)):
        pos = [0] * DIMS[k][0]
        for p, ch in enumerate(order[k]):
            pos[ch] = p
        rank.append(pos)

    w = []
    for out, inn in DIMS:
        w.append([[rng.gauss(0.0, 1.0 / math.sqrt(inn)) for _ in range(inn)] for _ in range(out)])

    gain = []
    shift = []
    for k, (out, _) in enumerate(DIMS):
        g = []
        s = []
        for i in range(out):
            if rank[k][i] < CORE[k]:
                g.append(1.0 + rng.gauss(0.0, 0.12))
                s.append(rng.gauss(0.0, 0.10))
            else:
                g.append(0.04 + 0.02 * rng.random())
                s.append(1.00 + 0.40 * rng.random())
        gain.append(g)
        shift.append(s)

    head_w = [
        [rng.gauss(0.0, 0.9 / math.sqrt(DIMS[-1][0])) for _ in range(DIMS[-1][0])]
        for _ in range(CLASSES)
    ]
    row_gain = [0.7, 1.6, 1.0, 2.2, 0.85]
    head_w = [[v * row_gain[c] for v in row] for c, row in enumerate(head_w)]
    head_b = [rng.gauss(0.0, 0.25) for _ in range(CLASSES)]
    return {
        "w": w,
        "gain": gain,
        "shift": shift,
        "head_w": head_w,
        "head_b": head_b,
        "order": order,
        "lane": rank,
    }


def moments(rows):
    n = len(rows)
    width = len(rows[0])
    mean = []
    var = []
    for i in range(width):
        s = 0.0
        for r in rows:
            s += r[i]
        m = s / n
        q = 0.0
        for r in rows:
            d = r[i] - m
            q += d * d
        mean.append(m)
        var.append(q / n)
    return mean, var


def head_logits(ck, acts, cols):
    out = []
    for a in acts:
        row = []
        for c in range(CLASSES):
            acc = ck["head_b"][c]
            hw = ck["head_w"][c]
            for pos, j in enumerate(cols):
                acc += hw[j] * a[pos]
            row.append(acc)
        out.append(row)
    return out


def run_stack(ck, rows, keep, stats):
    """Forward the (possibly pruned) stack under supplied per-layer stats."""
    prev = rows
    cols = list(range(IN_DIM))
    for layer in range(len(DIMS)):
        rows_keep = keep[layer]
        mean, var = stats[layer]
        act = []
        for a in prev:
            z = []
            for pos, i in enumerate(rows_keep):
                acc = 0.0
                wi = ck["w"][layer][i]
                for col, j in enumerate(cols):
                    acc += wi[j] * a[col]
                z.append(
                    relu(
                        ck["gain"][layer][i] * (acc - mean[pos]) / math.sqrt(var[pos] + EPS)
                        + ck["shift"][layer][i]
                    )
                )
            act.append(z)
        prev = act
        cols = rows_keep
    return prev, cols


def fit_stats(ck, rows, keep):
    """Sequential per-channel pre-norm moments over the calibration rows."""
    prev = rows
    cols = list(range(IN_DIM))
    stats = []
    for layer in range(len(DIMS)):
        rows_keep = keep[layer]
        pre = []
        for a in prev:
            z = []
            for i in rows_keep:
                acc = 0.0
                wi = ck["w"][layer][i]
                for col, j in enumerate(cols):
                    acc += wi[j] * a[col]
                z.append(acc)
            pre.append(z)
        mean, var = moments(pre)
        stats.append((mean, var))
        act = []
        for z in pre:
            act.append(
                [
                    relu(
                        ck["gain"][layer][i] * (z[pos] - mean[pos]) / math.sqrt(var[pos] + EPS)
                        + ck["shift"][layer][i]
                    )
                    for pos, i in enumerate(rows_keep)
                ]
            )
        prev = act
        cols = rows_keep
    return stats


def full_keep():
    return [list(range(out)) for out, _ in DIMS]


def slice_stats(stats, keep):
    return [
        ([stats[k][0][i] for i in keep[k]], [stats[k][1][i] for i in keep[k]])
        for k in range(len(DIMS))
    ]


def fit_head(ck, rows, keep, stats, ref_mean, ref_std):
    acts, cols = run_stack(ck, rows, keep, stats)
    mu, var = moments(head_logits(ck, acts, cols))
    out = []
    for c in range(CLASSES):
        sd = math.sqrt(var[c])
        s = ref_std[c] / sd if sd > 1e-12 else 1.0
        out.append((s, ref_mean[c] - s * mu[c]))
    return out


def argmax_rows(logits, refit):
    preds = []
    margins = []
    for row in logits:
        adj = [refit[c][0] * row[c] + refit[c][1] for c in range(CLASSES)] if refit else list(row)
        best = 0
        for c in range(1, CLASSES):
            if adj[c] > adj[best]:
                best = c
        top = sorted(adj, reverse=True)
        preds.append(best)
        margins.append(top[0] - top[1])
    return preds, margins


def score(ck, rows, labels, keep, stats, refit):
    acts, cols = run_stack(ck, rows, keep, stats)
    preds, margins = argmax_rows(head_logits(ck, acts, cols), refit)
    hit = sum(1 for p, y in zip(preds, labels) if p == y)
    return hit / len(labels), min(margins)


def geometry(keep, propagate=True):
    kept_p = kept_m = dense_p = dense_m = 0
    prev = IN_DIM
    for layer, (out, inn) in enumerate(DIMS):
        k_out = len(keep[layer])
        k_in = prev if propagate else inn
        kept_p += k_out * k_in
        kept_m += k_out * k_in * SPATIAL[layer]
        dense_p += out * inn
        dense_m += out * inn * SPATIAL[layer]
        prev = k_out
    last = len(keep[-1])
    kept_p += CLASSES * (last if propagate else DIMS[-1][0])
    kept_m += CLASSES * (last if propagate else DIMS[-1][0])
    dense_p += CLASSES * DIMS[-1][0]
    dense_m += CLASSES * DIMS[-1][0]
    return 1.0 - kept_p / dense_p, kept_m / dense_m


def keep_for(ck, counts):
    return [sorted(ck["order"][k][: counts[k]]) for k in range(len(DIMS))]


def build_world():
    ck = build_dense()
    ref = sample_rows(random.Random(99001), REF_N, 0.0, 1.0)
    dense_stats = fit_stats(ck, ref, full_keep())
    acts, cols = run_stack(ck, ref, full_keep(), dense_stats)
    ref_mean, ref_var = moments(head_logits(ck, acts, cols))
    ref_std = [math.sqrt(v) for v in ref_var]

    # a mid-run snapshot carries slightly different running stats
    drift = sample_rows(random.Random(31337), REF_N, 0.05, 1.12)
    resume_stats = fit_stats(ck, drift, full_keep())

    keeps = {tip: keep_for(ck, counts) for tip, (_, counts) in MASK_TIPS.items()}
    shards = {
        dom: sample_rows(random.Random(4200 + ord(dom)), CALIB_N, *DOMAINS[dom])
        for dom in DOMAINS
    }
    return ck, dense_stats, resume_stats, ref_mean, ref_std, keeps, shards


def dense_labels(ck, rows, dense_stats):
    acts, cols = run_stack(ck, rows, full_keep(), dense_stats)
    return argmax_rows(head_logits(ck, acts, cols), None)


def main():
    ck, dstats, rstats, ref_mean, ref_std, keeps, shards = build_world()
    keep = keeps["tip_g7"]

    for tip, (epoch, counts) in MASK_TIPS.items():
        sp, fl = geometry(keeps[tip])
        print(f"{tip} e={epoch} k={counts} sparsity={sp:.6f} flops={fl:.6f}")
    print("unpropagated g7:", [f"{v:.6f}" for v in geometry(keep, propagate=False)])

    calib = {"a": shards["a"], "b": shards["b"],
             "c": shards["a"] + shards["b"], "d": shards["a"] + shards["b"]}

    good_stats = {sid: fit_stats(ck, calib[sid], keep) for sid in calib}
    good_refit = {
        sid: fit_head(ck, calib[sid], keep, good_stats[sid], ref_mean, ref_std) for sid in calib
    }

    # eval slices, filtered so both the dense labeller and the recovered model
    # keep a comfortable argmax margin
    slices = {}
    for sid in ("a", "b", "c", "d"):
        rng = random.Random(7700 + ord(sid))
        rows = []
        labels = []
        tries = 0
        while len(rows) < EVAL_N and tries < 40000:
            tries += 1
            cand = mixed_rows(rng, 1) if sid in "cd" else sample_rows(rng, 1, *DOMAINS[sid])
            lab, dm = dense_labels(ck, cand, dstats)
            if dm[0] < MARGIN_FLOOR:
                continue
            acts, cols = run_stack(ck, cand, keep, good_stats[sid])
            _, gm = argmax_rows(head_logits(ck, acts, cols), good_refit[sid])
            if gm[0] < MARGIN_FLOOR:
                continue
            rows.append(cand[0])
            labels.append(lab[0])
        slices[sid] = (rows, labels)
        print(f"slice_{sid}: {len(rows)} rows after {tries} draws")

    print("\ncorrect pipeline")
    for sid in ("a", "b", "c", "d"):
        rows, labels = slices[sid]
        acc, m = score(ck, rows, labels, keep, good_stats[sid], good_refit[sid])
        print(f"  {sid}: acc={acc:.4f} margin={m:.4g}")

    print("\nablation: checkpoint stats, no recalibration")
    for sid in ("a", "b", "c", "d"):
        rows, labels = slices[sid]
        st = slice_stats(dstats, keep)
        rf = fit_head(ck, calib[sid], keep, st, ref_mean, ref_std)
        print(f"  {sid}: acc={score(ck, rows, labels, keep, st, rf)[0]:.4f}")

    print("\nablation: no head refit")
    for sid in ("a", "b", "c", "d"):
        rows, labels = slices[sid]
        print(f"  {sid}: acc={score(ck, rows, labels, keep, good_stats[sid], None)[0]:.4f}")

    print("\nablation: mix calibrated on one shard")
    for sid in ("c", "d"):
        rows, labels = slices[sid]
        st = fit_stats(ck, shards["a"], keep)
        rf = fit_head(ck, shards["a"], keep, st, ref_mean, ref_std)
        print(f"  {sid}: acc={score(ck, rows, labels, keep, st, rf)[0]:.4f}")

    print("\nablation: resume snapshot stats")
    for sid in ("a", "b"):
        rows, labels = slices[sid]
        st = slice_stats(rstats, keep)
        rf = fit_head(ck, calib[sid], keep, st, ref_mean, ref_std)
        print(f"  {sid}: acc={score(ck, rows, labels, keep, st, rf)[0]:.4f}")

    for tip in ("tip_g2", "tip_g5", "tip_g9", "tip_live"):
        print(f"\nablation: {tip}")
        for sid in ("a", "b", "c", "d"):
            rows, labels = slices[sid]
            k = keeps[tip]
            st = fit_stats(ck, calib[sid], k)
            rf = fit_head(ck, calib[sid], k, st, ref_mean, ref_std)
            print(f"  {sid}: acc={score(ck, rows, labels, k, st, rf)[0]:.4f}")


if __name__ == "__main__":
    main()
