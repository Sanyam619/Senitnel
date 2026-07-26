"""Emit the frozen fixtures for tasks/structured-prune-recovery-eval."""

from __future__ import annotations

import json
import random
from pathlib import Path

from reference_model import (
    CLASSES,
    DIMS,
    DOMAINS,
    EPS,
    EVAL_N,
    MARGIN_FLOOR,
    MASK_TIPS,
    SPATIAL,
    argmax_rows,
    build_dense,
    build_world,
    dense_labels,
    fit_head,
    fit_stats,
    full_keep,
    geometry,
    head_logits,
    mixed_rows,
    run_stack,
    sample_rows,
    score,
)

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "structured-prune-recovery-eval"
ENV = ROOT / "environment"

SLICE_DOMAINS = {"slice_a": ["a"], "slice_b": ["b"], "slice_c": ["a", "b"], "slice_d": ["a", "b"]}
ROSTER = [
    ("cold_a", "slice_a", "cold"),
    ("resume_a", "slice_a", "resume"),
    ("cold_b", "slice_b", "cold"),
    ("resume_b", "slice_b", "resume"),
    ("mix_c", "slice_c", "cold"),
    ("mix_d", "slice_d", "resume"),
]
JOURNAL = [
    (2, "tip_g2", "durable", "m_g2.txt"),
    (3, "tip_g3", "staged", "m_g3.txt"),
    (5, "tip_g5", "durable", "m_g5.txt"),
    (4, "tip_g4", "staged", "m_g4.txt"),
    (7, "tip_g7", "durable", "m_g7.txt"),
    (9, "tip_g9", "durable", "m_g9.txt"),
    (11, "tip_live", "staged", "overlay.txt"),
]
RETIRED = [("tip_g9", "channel roster rolled back after the reshape run")]
BOUND = "tip_g7"


def nums(vals):
    return " ".join(repr(float(v)) for v in vals)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ckpt_text(ck, stats, ref_mean, ref_std, source, extra=()):
    out = ["format prck2", f"source {source}"]
    for layer, (out_ch, in_ch) in enumerate(DIMS):
        out.append(f"block {layer} {out_ch} {in_ch}")
    for layer in range(len(DIMS)):
        flat = [v for row in ck["w"][layer] for v in row]
        out.append(f"w {layer} {nums(flat)}")
        out.append(f"gain {layer} {nums(ck['gain'][layer])}")
        out.append(f"shift {layer} {nums(ck['shift'][layer])}")
        out.append(f"norm_mean {layer} {nums(stats[layer][0])}")
        out.append(f"norm_var {layer} {nums(stats[layer][1])}")
    out.append(f"head {CLASSES} {DIMS[-1][0]}")
    out.append(f"head_w {nums([v for row in ck['head_w'] for v in row])}")
    out.append(f"head_b {nums(ck['head_b'])}")
    out.append(f"logit_mean {nums(ref_mean)}")
    out.append(f"logit_std {nums(ref_std)}")
    out.extend(extra)
    return "\n".join(out) + "\n"


def main():
    ck, dstats, rstats, ref_mean, ref_std, keeps, shards = build_world()
    keep = keeps[BOUND]
    calib = {
        "slice_a": shards["a"],
        "slice_b": shards["b"],
        "slice_c": shards["a"] + shards["b"],
        "slice_d": shards["a"] + shards["b"],
    }
    good_stats = {s: fit_stats(ck, calib[s], keep) for s in calib}
    good_refit = {
        s: fit_head(ck, calib[s], keep, good_stats[s], ref_mean, ref_std) for s in calib
    }

    # ---- eval slices, filtered for stable argmax on both the labeller and the
    # recovered stack
    slices = {}
    for sid, doms in SLICE_DOMAINS.items():
        tag = sid.split("_")[1]
        rng = random.Random(7700 + ord(tag))
        rows, labels = [], []
        while len(rows) < EVAL_N:
            cand = mixed_rows(rng, 1) if len(doms) > 1 else sample_rows(rng, 1, *DOMAINS[doms[0]])
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

    # ---- reference metrics
    sparsity, flops = geometry(keep)
    acc = {}
    for sid in SLICE_DOMAINS:
        acc[sid], _ = score(ck, *slices[sid], keep, good_stats[sid], good_refit[sid])

    # ---------------------------------------------------------------- topology
    topo = ["revision prune-topology-1", f"eps {EPS!r}", f"classes {CLASSES}"]
    for layer, (out_ch, in_ch) in enumerate(DIMS):
        topo.append(f"block block{layer} {out_ch} {in_ch} {SPATIAL[layer]}")
    write(ENV / "data/arch/topology.txt", "\n".join(topo) + "\n")

    # -------------------------------------------------------------- checkpoints
    write(
        ENV / "data/dense/cold.ckpt",
        ckpt_text(ck, dstats, ref_mean, ref_std, "dense-freeze"),
    )
    write(
        ENV / "data/dense/resume.ckpt",
        ckpt_text(
            ck,
            rstats,
            ref_mean,
            ref_std,
            "dense-step-snapshot",
            extra=["step 4200", "mask_stamp tip_g2"],
        ),
    )
    # pre-freeze weights nobody scores against
    stale = build_dense(seed=4041)
    stale_stats = fit_stats(stale, sample_rows(random.Random(5), 128, 0.0, 1.0), full_keep())
    write(
        ENV / "data/dense/legacy.ckpt",
        ckpt_text(stale, stale_stats, ref_mean, ref_std, "pre-freeze-archive"),
    )

    # -------------------------------------------------------------------- masks
    for tip, (epoch, counts) in MASK_TIPS.items():
        idx = keeps[tip]
        name = "overlay.txt" if tip == "tip_live" else f"m_{tip.split('_')[1]}.txt"
        kind = "overlay" if tip == "tip_live" else "structured"
        body = [f"tip {tip}", f"epoch {epoch}", f"kind {kind}"]
        for layer in range(len(DIMS)):
            body.append(f"keep {layer} " + " ".join(str(v) for v in idx[layer]))
        write(ENV / "data/masks" / name, "\n".join(body) + "\n")
    # staged sheets referenced by staged journal rows
    for tip, counts in (("tip_g3", [8, 9, 6]), ("tip_g4", [14, 15, 11])):
        rng = random.Random(hash(tip) % 9999)
        body = [f"tip {tip}", f"epoch {int(tip[-1])}", "kind structured"]
        for layer, (dim, _) in enumerate(DIMS):
            body.append(
                f"keep {layer} " + " ".join(str(v) for v in sorted(rng.sample(range(dim), counts[layer])))
            )
        write(ENV / f"data/masks/m_{tip.split('_')[1]}.txt", "\n".join(body) + "\n")

    # ----------------------------------------------------------------- registry
    lines = [
        json.dumps({"epoch": e, "tip": t, "state": s, "sheet": f})
        for e, t, s, f in JOURNAL
    ]
    write(ENV / "data/mask_registry/tip_journal.jsonl", "\n".join(lines) + "\n")
    write(
        ENV / "data/mask_registry/retired_tips.jsonl",
        "\n".join(json.dumps({"tip": t, "note": n}) for t, n in RETIRED) + "\n",
    )

    # -------------------------------------------------------------- calib shards
    for dom in DOMAINS:
        body = [f"id shard_{dom}", f"domain {dom}", f"count {len(shards[dom])}"]
        for row in shards[dom]:
            body.append("row " + nums(row))
        write(ENV / f"data/calib/shard_{dom}.txt", "\n".join(body) + "\n")

    # --------------------------------------------------------------- eval slices
    for sid, doms in SLICE_DOMAINS.items():
        rows, labels = slices[sid]
        body = [f"id {sid}", "domain " + " ".join(doms), f"count {len(rows)}"]
        for row, lab in zip(rows, labels):
            body.append("row " + nums(row) + f" {lab}")
        write(ENV / f"data/eval/{sid}.txt", "\n".join(body) + "\n")

    write(
        ENV / "data/eval/roster.txt",
        "\n".join(f"scenario {sid} {sl} {st}" for sid, sl, st in ROSTER) + "\n",
    )

    # ------------------------------------------------------------------- report
    print(f"sparsity={sparsity!r} flops={flops!r}")
    for sid in SLICE_DOMAINS:
        print(f"{sid}: acc={acc[sid]!r}")
    summary = {
        "sparsity": sparsity,
        "flops": flops,
        "accuracy": acc,
        "kept_channels": sum(len(k) for k in keep),
        "bound": BOUND,
        "bound_epoch": MASK_TIPS[BOUND][0],
    }
    Path(__file__).with_name("summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
