"""Emit the frozen fixtures for tasks/int4-weight-only-calibration-eval."""

from __future__ import annotations

import json
import random
from pathlib import Path

import reference_model as rm

ROOT = Path(__file__).resolve().parents[2] / "tasks" / "int4-weight-only-calibration-eval"
ENV = ROOT / "environment"

SLICES = {"slice_a": ["a"], "slice_b": ["b"], "slice_c": ["a", "b"], "slice_d": ["b", "a"]}
ROSTER = [
    ("cold_a", "slice_a", "cold"),
    ("resume_a", "slice_a", "resume"),
    ("cold_b", "slice_b", "cold"),
    ("resume_b", "slice_b", "resume"),
    ("mix_c", "slice_c", "cold"),
    ("mix_d", "slice_d", "resume"),
]
STARTS = {"cold": "cold.ckpt", "resume": "resume.ckpt"}
# Journal order is the order the desk saw the rows, not epoch order.
JOURNAL = ["tip_g4", "tip_live", "tip_g7", "tip_g2", "tip_g9", "tip_g6", "tip_g11", "tip_g5"]
SHEET = {
    "tip_g2": "grid_g2.txt",
    "tip_g4": "grid_g4.txt",
    "tip_g5": "grid_g5.txt",
    "tip_g6": "grid_g6.txt",
    "tip_g7": "grid_g7.txt",
    "tip_g9": "grid_g9.txt",
    "tip_g11": "grid_g11.txt",
    "tip_live": "grid_live.txt",
}
BANK = {tip: f"bank_{tip.split('_')[1]}.txt" for tip in SHEET}
RESUME_REF = "bank_g4.txt"


def nums(vals):
    return " ".join(repr(float(v)) for v in vals)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ckpt_text(ck, source, extra=()):
    out = ["format fp16ck1", f"source {source}"]
    for at, (w, b) in enumerate(rm.layers(ck)):
        out.append(f"w {at} " + nums(v for row in w for v in row))
        out.append(f"b {at} " + nums(b))
    out.extend(extra)
    return "\n".join(out) + "\n"


def build_slices(ck):
    out = {}
    for sid, doms in SLICES.items():
        tag = sid.split("_")[1]
        rng = random.Random(5100 + ord(tag))
        rows = []
        marks = []
        while len(rows) < rm.EVAL_N:
            cand = (
                rm.mixed_rows(rng, 1, doms[0])
                if len(doms) > 1
                else rm.sample_rows(rng, 1, *rm.DOMAINS[doms[0]])
            )
            lab, gap = rm.labels_of(ck, cand)
            if gap[0] < rm.MARGIN_FLOOR:
                continue
            rows.append(cand[0])
            marks.append(lab[0])
        out[sid] = (rows, marks)
    return out


def main():
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

    bound = rm.resolve()
    epoch, _, _, group = rm.TIPS[bound]
    gains = rm.fit_gains(ck, rows_for(rm.admitted(epoch)))
    model = rm.quantized(ck, gains, group)
    metrics = {sid: rm.measure(model, *slices[sid]) for sid in SLICES}

    # ------------------------------------------------------------------ layout
    layout = ["revision int4-layout-1", f"eps {rm.EPS!r}", f"classes {rm.CLASSES}"]
    for at in range(len(rm.IN_DIMS)):
        layout.append(f"layer {at} {rm.OUT_DIMS[at]} {rm.IN_DIMS[at]}")
    write(ENV / "data/arch/topology.txt", "\n".join(layout) + "\n")

    # ------------------------------------------------------------- checkpoints
    write(ENV / "data/fp16/cold.ckpt", ckpt_text(ck, "cold", extra=["step 0"]))
    write(
        ENV / "data/fp16/resume.ckpt",
        ckpt_text(
            ck,
            "resume",
            extra=["step 5200", "grid_stamp tip_g4", f"scale_ref {RESUME_REF}"],
        ),
    )
    stale = rm.build_fp16(seed=880417)
    write(ENV / "data/fp16/archive.ckpt", ckpt_text(stale, "archive", extra=["step 1900"]))

    # ------------------------------------------------------------ group sheets
    for tip, (ep, _state, kind, grp) in rm.TIPS.items():
        body = [f"tip {tip}", f"epoch {ep}", f"kind {kind}", f"group {grp}"]
        write(ENV / "data/quant_grids" / SHEET[tip], "\n".join(body) + "\n")

    # ---------------------------------------------------------------- registry
    rows = []
    for tip in JOURNAL:
        ep, state, kind, _grp = rm.TIPS[tip]
        rows.append(
            json.dumps(
                {
                    "epoch": ep,
                    "tip": tip,
                    "state": state,
                    "kind": kind,
                    "grid": SHEET[tip],
                    "bank": BANK[tip],
                }
            )
        )
    write(ENV / "data/quant_registry/tip_journal.jsonl", "\n".join(rows) + "\n")
    write(
        ENV / "data/quant_registry/retired_tips.jsonl",
        "\n".join(
            json.dumps({"tip": t, "note": "grouping sheet rolled back after the sweep"})
            for t in rm.RETIRED
        )
        + "\n",
    )

    # ----------------------------------------------------------- captured banks
    # Revision 2 of the calibration desk folded the probe shard into every
    # capture; the current revision does not.
    for tip in rm.TIPS:
        ep = rm.TIPS[tip][0]
        names = sorted(set(rm.admitted(ep)) | {"shard_d"})
        cap = rm.fit_gains(ck, rows_for(names))
        body = [f"id {BANK[tip].split('.')[0]}", "revision cal-rev2"]
        for at, vals in enumerate(cap):
            body.append(f"gain {at} " + nums(vals))
        write(ENV / "data/scales" / BANK[tip], "\n".join(body) + "\n")

    # ----------------------------------------------------------- calib material
    for name in sorted(rm.ADMIT):
        body = [f"id {name}", f"domain {name.split('_')[1]}", f"count {len(shards[name])}"]
        for row in shards[name]:
            body.append("row " + nums(row))
        write(ENV / f"data/calib/{name}.txt", "\n".join(body) + "\n")
    write(
        ENV / "data/calib/admit_ledger.jsonl",
        "\n".join(
            json.dumps({"shard": s, "first": rm.ADMIT[s][0], "last": rm.ADMIT[s][1]})
            for s in sorted(rm.ADMIT)
        )
        + "\n",
    )

    # ------------------------------------------------------------- eval slices
    for sid, doms in SLICES.items():
        rows, marks = slices[sid]
        body = [f"id {sid}", "domain " + " ".join(doms), f"count {len(rows)}"]
        for row, mark in zip(rows, marks):
            body.append("row " + nums(row) + f" {mark}")
        write(ENV / f"data/eval/{sid}.txt", "\n".join(body) + "\n")
    write(
        ENV / "data/eval/roster.txt",
        "\n".join(f"scenario {sid} {sl}.txt {STARTS[st]}" for sid, sl, st in ROSTER) + "\n",
    )

    # --------------------------------------------------------------- ablations
    def run(names, grp, packer=rm.pack, sheet=None):
        g = sheet if sheet is not None else rm.fit_gains(ck, rows_for(names))
        mdl = rm.quantized(ck, g, grp, packer)
        return {sid: rm.measure(mdl, *slices[sid]) for sid in SLICES}

    def captured(tip):
        names = sorted(set(rm.admitted(rm.TIPS[tip][0])) | {"shard_d"})
        return rm.fit_gains(ck, rows_for(names))

    ablate = {
        "faithful": metrics,
        "live_per_channel": run(rm.admitted(12), 32),
        "retired_g9": run(rm.admitted(9), 4),
        "sealed_per_channel_g11": run(rm.admitted(11), 32),
        "all_shards": run(sorted(rm.ADMIT), group),
        "captured_bank": run(None, group, sheet=captured(bound)),
        "rowwise_pack": run(rm.admitted(epoch), group, rm.pack_rowwise),
        "resume_stamped_bank": run(None, group, sheet=captured("tip_g4")),
        "g4_width": run(rm.admitted(epoch), 4),
        "g2_width": run(rm.admitted(epoch), 2),
    }

    # -------------------------------------------------------- captured sweep
    # A sweep the desk kept from the live per-channel generation. Every number
    # sits inside the published bands; none of them is a scoring pass.
    sweep = {
        "schema_tag": "int4-eval-v1",
        "captured": "sweep-live-2",
        "scenarios": [
            {
                "id": sid,
                "perplexity": round(metrics[sl][0] * 1.0118, 6),
                "top1": round(metrics[sl][1] - 0.00625, 6),
                "group_size": rm.TIPS["tip_live"][3],
                "tip_epoch": rm.TIPS["tip_live"][0],
            }
            for sid, sl, _ in ROSTER
        ],
        "bands_ok": True,
    }
    write(ENV / "data/fixtures/surface_ok.json", json.dumps(sweep, indent=2) + "\n")

    # ------------------------------------------------------------------ report
    summary = {
        "bound": bound,
        "epoch": epoch,
        "group": group,
        "grid_span": rm.grid_span(group),
        "admitted": rm.admitted(epoch),
        "metrics": {sid: {"ppl": metrics[sid][0], "top1": metrics[sid][1]} for sid in SLICES},
        "scenarios": {
            sid: {"ppl": metrics[sl][0], "top1": metrics[sl][1]} for sid, sl, _ in ROSTER
        },
        "span": {g: rm.grid_span(g) for g in (2, 4, 8, 32)},
        "ablations": {
            name: {sid: {"ppl": v[0], "top1": v[1]} for sid, v in table.items()}
            for name, table in ablate.items()
        },
    }
    Path(__file__).with_name("summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
