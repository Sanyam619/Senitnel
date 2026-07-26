"""Explore the band separation before the fixtures are frozen."""

from __future__ import annotations

import random

from reference_model import (
    ADMIT,
    CALIB_N,
    DOMAINS,
    EVAL_N,
    MARGIN_FLOOR,
    TIPS,
    admitted,
    build_fp16,
    fit_gains,
    grid_span,
    labels_of,
    measure,
    mixed_rows,
    pack,
    pack_rowwise,
    quantized,
    resolve,
    sample_rows,
)

SLICES = {"slice_a": ["a"], "slice_b": ["b"], "slice_c": ["a", "b"], "slice_d": ["b", "a"]}


def build_slices(ck):
    out = {}
    for sid, doms in SLICES.items():
        tag = sid.split("_")[1]
        rng = random.Random(5100 + ord(tag))
        rows = []
        marks = []
        while len(rows) < EVAL_N:
            cand = (
                mixed_rows(rng, 1, doms[0])
                if len(doms) > 1
                else sample_rows(rng, 1, *DOMAINS[doms[0]])
            )
            lab, gap = labels_of(ck, cand)
            if gap[0] < MARGIN_FLOOR:
                continue
            rows.append(cand[0])
            marks.append(lab[0])
        out[sid] = (rows, marks)
    return out


def main():
    ck = build_fp16()
    shards = {
        f"shard_{d}": sample_rows(random.Random(3300 + ord(d)), CALIB_N[d], *DOMAINS[d])
        for d in ("a", "b")
    }
    shards["shard_c"] = sample_rows(random.Random(3300 + ord("c")), CALIB_N["c"], 0.55, 1.35)
    shards["shard_d"] = sample_rows(random.Random(3300 + ord("d")), CALIB_N["d"], -0.45, 0.80)

    slices = build_slices(ck)
    bound = resolve()
    epoch, _, _, group = TIPS[bound]
    print(f"bound={bound} epoch={epoch} group={group} span={grid_span(group)}")
    print("admitted@7:", admitted(epoch), " admitted@14:", admitted(14))

    def rows_for(names):
        out = []
        for s in names:
            out.extend(shards[s])
        return out

    good_gains = fit_gains(ck, rows_for(admitted(epoch)))
    good = quantized(ck, good_gains, group)

    print("\nfp16 reference")
    for sid in SLICES:
        rows, marks = slices[sid]
        print(f"  {sid}: {measure(ck, rows, marks)}")

    print("\nfaithful int4 pass")
    ref = {}
    for sid in SLICES:
        rows, marks = slices[sid]
        ref[sid] = measure(good, rows, marks)
        print(f"  {sid}: ppl={ref[sid][0]:.6f} top1={ref[sid][1]:.6f}")

    def report(label, model):
        line = []
        for sid in SLICES:
            rows, marks = slices[sid]
            p, t = measure(model, rows, marks)
            line.append(f"{sid} ppl={p:.4f}({p - ref[sid][0]:+.4f}) top1={t:.4f}({t - ref[sid][1]:+.4f})")
        print(f"  {label}\n     " + "\n     ".join(line))

    print("\nablations")
    for tip, (ep, state, kind, grp) in sorted(TIPS.items(), key=lambda kv: kv[1][0]):
        g = fit_gains(ck, rows_for(admitted(ep)))
        report(f"tip {tip} e={ep} {state}/{kind} group={grp}", quantized(ck, g, grp))

    report("all shards admitted", quantized(ck, fit_gains(ck, rows_for(sorted(ADMIT))), group))
    report(
        "window widened by shard_c",
        quantized(ck, fit_gains(ck, rows_for(["shard_a", "shard_b", "shard_c"])), group),
    )
    report(
        "captured bank revision (a+b+d)",
        quantized(ck, fit_gains(ck, rows_for(["shard_a", "shard_b", "shard_d"])), group),
    )
    report("row-wise group extent", quantized(ck, good_gains, group, packer=pack_rowwise))
    report("no activation scaling", quantized(ck, [[1.0] * len(g) for g in good_gains], group))
    report("novel generation e=14 group=4", quantized(ck, fit_gains(ck, rows_for(admitted(14))), 4))
    print("grid_span(4) =", grid_span(4), " grid_span(32) =", grid_span(32))
    assert pack is not None


if __name__ == "__main__":
    main()
