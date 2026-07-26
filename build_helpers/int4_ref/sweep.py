"""Pick (SHARP, OUTLIER_RATE, OUTLIER_GAIN) with clean band separation."""

from __future__ import annotations

import random

import reference_model as rm
from tune import SLICES, build_slices


def evaluate():
    ck = rm.build_fp16()
    shards = {
        f"shard_{d}": rm.sample_rows(random.Random(3300 + ord(d)), rm.CALIB_N[d], *rm.DOMAINS[d])
        for d in ("a", "b")
    }
    shards["shard_c"] = rm.sample_rows(random.Random(3300 + ord("c")), rm.CALIB_N["c"], 0.55, 1.35)
    shards["shard_d"] = rm.sample_rows(random.Random(3300 + ord("d")), rm.CALIB_N["d"], -0.45, 0.80)
    slices = build_slices(ck)

    def rows_for(names):
        out = []
        for s in names:
            out.extend(shards[s])
        return out

    good_gains = rm.fit_gains(ck, rows_for(rm.admitted(7)))
    good = rm.quantized(ck, good_gains, 8)
    ref = {sid: rm.measure(good, *slices[sid]) for sid in SLICES}

    variants = {
        "group4@7": rm.quantized(ck, good_gains, 4),
        "group32@11": rm.quantized(ck, rm.fit_gains(ck, rows_for(rm.admitted(11))), 32),
        "group32@12": rm.quantized(ck, rm.fit_gains(ck, rows_for(rm.admitted(12))), 32),
        "group4@9": rm.quantized(ck, rm.fit_gains(ck, rows_for(rm.admitted(9))), 4),
        "allshards": rm.quantized(ck, rm.fit_gains(ck, rows_for(sorted(rm.ADMIT))), 8),
        "widened": rm.quantized(
            ck, rm.fit_gains(ck, rows_for(["shard_a", "shard_b", "shard_c"])), 8
        ),
        "capturedrev": rm.quantized(
            ck, rm.fit_gains(ck, rows_for(["shard_a", "shard_b", "shard_d"])), 8
        ),
        "rowwise": rm.quantized(ck, good_gains, 8, packer=rm.pack_rowwise),
        "flatgains": rm.quantized(ck, [[1.0] * len(g) for g in good_gains], 8),
        "novel14g4": rm.quantized(ck, rm.fit_gains(ck, rows_for(rm.admitted(14))), 4),
    }

    worst_ppl = 1e9
    worst_name = ""
    for name, model in variants.items():
        for sid in SLICES:
            p, t = rm.measure(model, *slices[sid])
            gap = abs(p - ref[sid][0])
            if gap < worst_ppl:
                worst_ppl = gap
                worst_name = f"{name}/{sid}"
    novel = {sid: rm.measure(variants["novel14g4"], *slices[sid]) for sid in SLICES}
    return ref, worst_ppl, worst_name, novel


def main():
    grid = [
        (3.0, 0.06, 6.0),
        (3.0, 0.07, 6.5),
        (3.2, 0.06, 6.0),
        (3.2, 0.07, 7.0),
        (2.9, 0.07, 5.5),
        (3.1, 0.05, 6.5),
    ]
    for sharp, rate, gain in grid:
        rm.SHARP, rm.OUTLIER_RATE, rm.OUTLIER_GAIN = sharp, rate, gain
        ref, worst, name, novel = evaluate()
        top1 = [ref[s][1] for s in SLICES]
        ppl = [ref[s][0] for s in SLICES]
        print(
            f"SHARP={sharp} rate={rate} gain={gain} | "
            f"ppl={[round(v, 3) for v in ppl]} top1={[round(v, 3) for v in top1]} | "
            f"min|dppl|={worst:.4f} at {name} | "
            f"novel ppl={[round(novel[s][0], 3) for s in SLICES]}"
        )


if __name__ == "__main__":
    main()
