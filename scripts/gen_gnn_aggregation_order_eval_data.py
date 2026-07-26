"""Generate frozen GNN graphs + checkpoints for gnn-aggregation-order-eval.

Run from repo: python3 scripts/gen_gnn_aggregation_order_eval_data.py
Writes under tasks/gnn-aggregation-order-eval/environment/data/.
Also prints EXPECTED metrics for the oracle path.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parents[1]
    / "tasks"
    / "gnn-aggregation-order-eval"
    / "environment"
    / "data"
)
DIM = 4
N_CLASS = 3
SEED = 20260725


def rng(seed: int):
    x = seed & 0xFFFFFFFF

    def nxt():
        nonlocal x
        x = (1664525 * x + 1013904223) & 0xFFFFFFFF
        return x

    return nxt


def f32s(vals):
    return b"".join(struct.pack("<f", float(v)) for v in vals)


def write_graph(path: Path, n: int, edges: list[tuple[int, int]], feats: list[list[float]], labels: list[int]):
    e = len(edges)
    blob = bytearray()
    blob += b"GPH1"
    blob += struct.pack("<IIII", n, e, DIM, N_CLASS)
    for row in feats:
        blob += f32s(row)
    blob += struct.pack("<" + "H" * n, *labels)
    for u, v in edges:
        blob += struct.pack("<II", u, v)
    path.write_bytes(blob)


def read_graph(path: Path):
    blob = path.read_bytes()
    assert blob[:4] == b"GPH1"
    n, e, d, _nc = struct.unpack_from("<IIII", blob, 4)
    off = 20
    feats = []
    for _ in range(n):
        row = list(struct.unpack_from("<" + "f" * d, blob, off))
        off += 4 * d
        feats.append(row)
    labels = list(struct.unpack_from("<" + "H" * n, blob, off))
    off += 2 * n
    edges = []
    for _ in range(e):
        u, v = struct.unpack_from("<II", blob, off)
        off += 8
        edges.append((u, v))
    return n, edges, feats, labels


def degrees(n: int, edges: list[tuple[int, int]]):
    deg = [0] * n
    for u, v in edges:
        deg[u] += 1
        if u != v:
            deg[v] += 1
    return [float(x) for x in deg]


def adj_list(n: int, edges: list[tuple[int, int]]):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        if u != v:
            adj[v].append(u)
    for i in range(n):
        adj[i] = sorted(set(adj[i]))
        if i not in adj[i]:
            adj[i].append(i)
            adj[i].sort()
    return adj


def braid_n(rows, deg, pref: str):
    out = []
    for i, row in enumerate(rows):
        if pref == "degree":
            s = math.sqrt(deg[i] + 1.0)
            out.append([v / s for v in row])
        else:
            out.append(list(row))
    return out


def aggregate(vecs, mode: str):
    if not vecs:
        return [0.0] * DIM
    d = len(vecs[0])
    if mode == "sum":
        return [sum(v[j] for v in vecs) for j in range(d)]
    if mode == "max":
        return [max(v[j] for v in vecs) for j in range(d)]
    if mode == "pna":
        mn = [sum(v[j] for v in vecs) / len(vecs) for j in range(d)]
        mx = [max(v[j] for v in vecs) for j in range(d)]
        return [mn[j] + mx[j] for j in range(d)]
    # mean
    return [sum(v[j] for v in vecs) / len(vecs) for j in range(d)]


def message_pass(feats, edges, agg: str, pref: str):
    n = len(feats)
    deg = degrees(n, edges)
    seated = braid_n(feats, deg, pref)
    adj = adj_list(n, edges)
    out = []
    for i in range(n):
        vecs = [seated[j] for j in adj[i]]
        out.append(aggregate(vecs, agg))
    return out


def matmul(hs, weights):
    # weights: n_class rows of DIM
    logits = []
    for h in hs:
        row = []
        for w in weights:
            row.append(sum(h[j] * w[j] for j in range(DIM)))
        logits.append(row)
    return logits


def predict(logits):
    return [max(range(len(row)), key=lambda k: row[k]) for row in logits]


def soft_accuracy(logits, y):
    if not y:
        return 0.0
    total = 0.0
    for logit, lab in zip(logits, y):
        m = max(logit)
        exps = [math.exp(v - m) for v in logit]
        z = sum(exps)
        total += exps[lab] / z
    return total / len(y)


def macro_f1(yhat, y):
    scores = []
    for c in range(N_CLASS):
        tp = sum(1 for a, b in zip(yhat, y) if a == c and b == c)
        fp = sum(1 for a, b in zip(yhat, y) if a == c and b != c)
        fn = sum(1 for a, b in zip(yhat, y) if a != c and b == c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        scores.append(f1)
    return sum(scores) / N_CLASS


def score_graph(feats, edges, labels, weights, agg: str, pref: str):
    hs = message_pass(feats, edges, agg, pref)
    logits = matmul(hs, weights)
    yhat = predict(logits)
    return soft_accuracy(logits, labels), macro_f1(yhat, labels)


def fold_graphs(parts: list[tuple]):
    """Union disconnected graphs."""
    feats = []
    labels = []
    edges = []
    off = 0
    for n, e, f, lab in parts:
        feats.extend(f)
        labels.extend(lab)
        for u, v in e:
            edges.append((u + off, v + off))
        off += n
    return len(feats), edges, feats, labels


def write_ckp1(path: Path, weights: list[list[float]]):
    n = len(weights)
    blob = bytearray()
    blob += b"CKP1"
    blob += struct.pack("<II", n, DIM)
    # pad tags
    blob += struct.pack("<" + "H" * n, *([0] * n))
    for row in weights:
        blob += f32s(row)
    path.write_bytes(blob)


def write_ckp2(path: Path, weights: list[list[float]], block: int, coefs: list[float]):
    n = len(weights)
    blob = bytearray()
    blob += b"CKP2"
    blob += struct.pack("<III", n, DIM, block)
    blob += struct.pack("<" + "H" * n, *([0] * n))
    done = 0
    ci = 0
    while done < n:
        take = min(block, n - done)
        coef = coefs[ci] if ci < len(coefs) else 1.0
        ci += 1
        blob += struct.pack("<f", coef)
        for i in range(done, done + take):
            # store pre-divided so correct decode multiplies by coef
            row = [v / coef for v in weights[i]]
            blob += f32s(row)
        done += take
    path.write_bytes(blob)


def lens_unfold(blob: bytes) -> list[list[float]]:
    magic = blob[:4]
    if magic == b"CKP1":
        n, d = struct.unpack_from("<II", blob, 4)
        off = 12 + 2 * n
        rows = []
        for _ in range(n):
            rows.append(list(struct.unpack_from("<" + "f" * d, blob, off)))
            off += 4 * d
        return rows
    if magic == b"CKP2":
        n, d, block = struct.unpack_from("<III", blob, 4)
        off = 16 + 2 * n
        rows = []
        done = 0
        while done < n and block > 0:
            coef = struct.unpack_from("<f", blob, off)[0]
            off += 4
            take = min(block, n - done)
            for _ in range(take):
                row = list(struct.unpack_from("<" + "f" * d, blob, off))
                off += 4 * d
                rows.append([v * coef for v in row])  # correct
            done += take
        return rows
    return []


def make_family(seed: int, n: int, name_prefix: str, out_dir: Path, ids: list[int], noise: float):
    del name_prefix
    r = rng(seed)
    paths = []
    assert n % N_CLASS == 0
    per = n // N_CLASS
    for gid in ids:
        labels = []
        for c in range(N_CLASS):
            labels.extend([c] * per)
        edges: list[tuple[int, int]] = []
        # star hubs inside each class (uneven degree) + a few peer edges
        for c in range(N_CLASS):
            base = c * per
            hub = base
            for i in range(1, per):
                edges.append((hub, base + i))
            for i in range(1, per - 1):
                if r() % 3 == 0:
                    edges.append((base + i, base + i + 1))
        # cross-class bridges — more when noise is high
        bridge_n = 2 + int(noise * 8)
        for _ in range(bridge_n):
            u = r() % n
            v = r() % n
            if u != v:
                edges.append((u, v))
        deg = degrees(n, edges)
        hub_cut = sorted(deg, reverse=True)[max(1, n // 5)]
        feats = []
        for i in range(n):
            lab = labels[i]
            row = [((r() % 1000) / 1000.0 - 0.5) * (0.20 + 0.5 * noise) for _ in range(DIM)]
            # Class bump is pre-scaled so degree-norm restores a unit signal.
            row[lab] += (1.25 - 0.4 * noise) * math.sqrt(deg[i] + 1.0)
            # Hub pollution is NOT pre-scaled: raw seating keeps it large and
            # the negative class weight on dim-3 then flips logits; degree-norm
            # shrinks it.
            if deg[i] >= hub_cut:
                row[3] += 3.2 + 1.5 * noise
            # Bridge nodes get a small opposing-class leak under high noise.
            if noise > 0.3 and (r() % 5 == 0):
                other = (lab + 1 + (r() % 2)) % N_CLASS
                row[other] += 0.55 * noise * math.sqrt(deg[i] + 1.0)
            feats.append(row)
        path = out_dir / f"graph_{gid:02d}.gbin"
        write_graph(path, n, edges, feats, labels)
        paths.append(path)
    return paths


def main():
    graphs = ROOT / "graphs"
    ckpts = ROOT / "checkpoints"
    registry = ROOT / "feature_registry"
    sched = ROOT / "sched"
    fixtures = ROOT / "fixtures"
    ledger = ROOT / "ledger"
    for p in (graphs, ckpts, registry, sched, fixtures, ledger):
        p.mkdir(parents=True, exist_ok=True)

    # Clean family graphs (1,2,5,6) vs noisier (3,4,7,8) so mix roster matters.
    make_family(SEED, 18, "a", graphs, [1, 2], noise=0.05)
    make_family(SEED + 17, 18, "a", graphs, [3, 4], noise=0.55)
    make_family(SEED + 99, 18, "b", graphs, [5, 6], noise=0.08)
    make_family(SEED + 140, 18, "b", graphs, [7, 8], noise=0.60)

    weights_a = [
        [1.0, -0.20, -0.20, -1.10],
        [-0.20, 1.0, -0.20, -1.10],
        [-0.20, -0.20, 1.0, -1.10],
    ]
    weights_b = [
        [1.0, -0.18, -0.22, -1.05],
        [-0.20, 1.0, -0.16, -1.08],
        [-0.22, -0.18, 1.0, -1.02],
    ]
    write_ckp1(ckpts / "cold_a.ckpt", weights_a)
    # Distinct per-row scales so skipping the multiply breaks class geometry.
    write_ckp2(ckpts / "resume_a.ckpt", weights_a, block=1, coefs=[0.25, 4.0, 0.25])
    write_ckp1(ckpts / "cold_b.ckpt", weights_b)
    write_ckp2(ckpts / "resume_b.ckpt", weights_b, block=1, coefs=[4.0, 0.25, 4.0])

    journal = [
        {
            "idx": 3,
            "state": "durable",
            "tip": "tip_g3",
            "agg": "sum",
            "norm": "degree",
            "sheet": "a7",
            "weft_c": ["graph_01", "graph_03", "graph_05", "graph_07"],
            "weft_d": ["graph_02", "graph_04", "graph_06", "graph_08"],
            "note": "quarterly refresh",
        },
        {
            "idx": 4,
            "state": "durable",
            "tip": "tip_g4",
            "agg": "mean",
            "norm": "degree",
            "sheet": "a7",
            "weft_c": ["graph_02", "graph_03", "graph_06", "graph_07"],
            "weft_d": ["graph_01", "graph_04", "graph_05", "graph_08"],
            "note": "post-ingest rebalance",
        },
        {"idx": 5, "state": "live", "tip": "tip_live", "agg": "max", "norm": "raw", "sheet": "w2", "note": "sweep prep"},
        {
            "idx": 6,
            "state": "durable",
            "tip": "tip_g7",
            "agg": "mean",
            "norm": "degree",
            "sheet": "a7",
            "weft_c": ["graph_01", "graph_02", "graph_05", "graph_06"],
            "weft_d": ["graph_03", "graph_04", "graph_07", "graph_08"],
            "note": "composition refresh",
        },
        {"idx": 7, "state": "live", "tip": "tip_live", "agg": "max", "norm": "raw", "sheet": "w2", "note": "recal sweep pass one"},
        {
            "idx": 8,
            "state": "durable",
            "tip": "tip_g9",
            "agg": "pna",
            "norm": "degree",
            "sheet": "a7",
            "weft_c": ["graph_01", "graph_04", "graph_06", "graph_07"],
            "weft_d": ["graph_02", "graph_03", "graph_05", "graph_08"],
            "note": "rolled tip",
        },
        {"idx": 9, "state": "live", "tip": "tip_live", "agg": "max", "norm": "raw", "sheet": "w2", "note": "recal sweep pass two"},
    ]
    (registry / "tip_journal.jsonl").write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in journal),
        encoding="utf-8",
    )
    (registry / "retired_tips.jsonl").write_text(
        '{"idx":5,"tip":"tip_g5"}\n{"idx":8,"tip":"tip_g9"}\n',
        encoding="utf-8",
    )

    (sched / "table_a7.toml").write_text(
        '# Committed aggregation sheet keyed by tip generation\n'
        '[rows]\n'
        '"3" = "sum"\n'
        '"4" = "mean"\n'
        '"6" = "mean"\n'
        '"8" = "pna"\n'
        '"10" = "sum"\n'
        '"11" = "sum"\n',
        encoding="utf-8",
    )
    (sched / "table_w2.toml").write_text(
        '# Alternate aggregation sheet keyed by tip generation\n'
        '[rows]\n'
        '"5" = "max"\n'
        '"7" = "max"\n'
        '"9" = "max"\n'
        '"8" = "pna"\n',
        encoding="utf-8",
    )

    (ledger / "journal.jsonl").write_text(
        '{"idx":9,"state":"live","tip":"tip_live","note":"prior entry"}\n',
        encoding="utf-8",
    )

    # Oracle path metrics
    tip_agg = "mean"
    tip_norm = "degree"
    tip_epoch = 6

    def load_named(names):
        parts = []
        for name in names:
            parts.append(read_graph(graphs / f"{name}.gbin"))
        return fold_graphs(parts)

    fam_a = fold_graphs([read_graph(graphs / f"graph_{i:02d}.gbin") for i in (1, 2, 3, 4)])
    fam_b = fold_graphs([read_graph(graphs / f"graph_{i:02d}.gbin") for i in (5, 6, 7, 8)])
    mix_c = load_named(["graph_01", "graph_02", "graph_05", "graph_06"])
    mix_d = load_named(["graph_03", "graph_04", "graph_07", "graph_08"])

    wa = lens_unfold((ckpts / "cold_a.ckpt").read_bytes())
    wa2 = lens_unfold((ckpts / "resume_a.ckpt").read_bytes())
    wb = lens_unfold((ckpts / "cold_b.ckpt").read_bytes())
    wb2 = lens_unfold((ckpts / "resume_b.ckpt").read_bytes())
    assert wa == wa2
    assert wb == wb2

    cells = {}
    for sid, part, w in [
        ("cold_a", fam_a, wa),
        ("resume_a", fam_a, wa2),
        ("cold_b", fam_b, wb),
        ("resume_b", fam_b, wb2),
        ("mix_c", mix_c, wa2),
        ("mix_d", mix_d, wb2),
    ]:
        _n, e, f, lab = part
        acc, f1 = score_graph(f, e, lab, w, tip_agg, tip_norm)
        cells[sid] = (acc, f1)
        print(f"{sid}: acc={acc:.6f} f1={f1:.6f}")

    # bait: shuffled neighbor order with max+raw that happens to look ok on cold_a-ish
    bait = {
        "schema_tag": "gnn-eval-v2",
        "scenarios": [],
        "bands_ok": True,
    }
    bait_vals = {
        "cold_a": (0.834170, 0.972222),
        "resume_a": (0.834170, 0.972222),
        "cold_b": (0.833218, 0.972174),
        "resume_b": (0.833218, 0.972174),
        "mix_c": (0.890850, 0.972482),
        "mix_d": (0.776405, 0.958296),
    }
    for sid in ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d"):
        a, f = bait_vals[sid]
        bait["scenarios"].append(
            {
                "id": sid,
                "accuracy": round(a, 6),
                "macro_f1": round(f, 6),
                "agg": "max",
                "tip_epoch": 9,
            }
        )
    (fixtures / "surface_ok.json").write_text(json.dumps(bait, indent=2) + "\n", encoding="utf-8")

    print("EXPECTED = {")
    for sid, (a, f) in cells.items():
        print(f'    "{sid}": ({a:.6f}, {f:.6f}),')
    print("}")
    print(f"AGG={tip_agg} EPOCH={tip_epoch}")


if __name__ == "__main__":
    main()
