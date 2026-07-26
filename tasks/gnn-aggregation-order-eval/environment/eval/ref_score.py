"""Faithful GNN eval reference for verifier / desk probes.

Reads frozen graphs and checkpoints under a data root and prints JSON
scenario metrics for a given aggregation mode, degree preference, and
mix rosters. Matches the seating rule in /app/docs/gnn_bands.md.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

DIM = 4
N_CLASS = 3


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


def fold(parts):
    feats = []
    labels = []
    edges = []
    base = 0
    for n, e, f, lab in parts:
        feats.extend(f)
        labels.extend(lab)
        edges.extend((u + base, v + base) for u, v in e)
        base += n
    return base, edges, feats, labels


def degrees(n, edges):
    deg = [0.0] * n
    for u, v in edges:
        deg[u] += 1.0
        if u != v:
            deg[v] += 1.0
    return deg


def adj_list(n, edges):
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


def braid_n(rows, deg, pref):
    out = []
    for i, row in enumerate(rows):
        if pref == "degree":
            scale = math.sqrt(deg[i] + 1.0)
            out.append([v / scale for v in row])
        else:
            out.append(list(row))
    return out


def aggregate(vecs, mode):
    width = len(vecs[0])
    if mode == "sum":
        return [sum(v[j] for v in vecs) for j in range(width)]
    if mode == "max":
        return [max(v[j] for v in vecs) for j in range(width)]
    if mode == "pna":
        n = len(vecs)
        return [
            sum(v[j] for v in vecs) / n + max(v[j] for v in vecs) for j in range(width)
        ]
    n = len(vecs)
    return [sum(v[j] for v in vecs) / n for j in range(width)]


def message_pass(feats, edges, agg, pref):
    n = len(feats)
    seated = braid_n(feats, degrees(n, edges), pref)
    adj = adj_list(n, edges)
    return [aggregate([seated[j] for j in adj[i]], agg) for i in range(n)]


def lens_unfold(blob: bytes):
    if len(blob) < 12:
        return []
    magic = blob[:4]
    off = 4
    n = struct.unpack_from("<I", blob, off)[0]
    off += 4
    dim = struct.unpack_from("<I", blob, off)[0]
    off += 4
    if magic == b"CKP1":
        off += 2 * n
        rows = []
        for _ in range(n):
            rows.append(list(struct.unpack_from("<" + "f" * dim, blob, off)))
            off += 4 * dim
        return rows
    if magic == b"CKP2":
        block = struct.unpack_from("<I", blob, off)[0]
        off += 4
        off += 2 * n
        rows = []
        done = 0
        while done < n and block > 0:
            coef = struct.unpack_from("<f", blob, off)[0]
            off += 4
            take = min(block, n - done)
            for _ in range(take):
                row = list(struct.unpack_from("<" + "f" * dim, blob, off))
                off += 4 * dim
                rows.append([v * coef for v in row])
            done += take
        return rows
    return []


def score(feats, edges, labels, weights, agg, pref):
    hs = message_pass(feats, edges, agg, pref)
    logits = [
        [sum(h[j] * w[j] for j in range(min(len(h), len(w)))) for w in weights]
        for h in hs
    ]
    yhat = [max(range(len(row)), key=lambda k: row[k]) for row in logits]
    total = 0.0
    for logit, lab in zip(logits, labels):
        peak = max(logit)
        exps = [math.exp(v - peak) for v in logit]
        z = sum(exps)
        total += exps[lab] / z
    acc = total / len(labels) if labels else 0.0
    scores = []
    for c in range(N_CLASS):
        tp = sum(1 for a, b in zip(yhat, labels) if a == c and b == c)
        fp = sum(1 for a, b in zip(yhat, labels) if a == c and b != c)
        fn = sum(1 for a, b in zip(yhat, labels) if a != c and b == c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        scores.append(f1)
    return acc, sum(scores) / N_CLASS


def reference_cells(data: Path, agg: str, norm: str, weft_c, weft_d):
    graphs = data / "graphs"
    ckpts = data / "checkpoints"

    def named(names):
        return fold([read_graph(graphs / f"{name}.gbin") for name in names])

    fam_a = fold([read_graph(graphs / f"graph_{i:02d}.gbin") for i in (1, 2, 3, 4)])
    fam_b = fold([read_graph(graphs / f"graph_{i:02d}.gbin") for i in (5, 6, 7, 8)])
    mix_c = named(weft_c)
    mix_d = named(weft_d)
    wa = lens_unfold((ckpts / "cold_a.ckpt").read_bytes())
    wa2 = lens_unfold((ckpts / "resume_a.ckpt").read_bytes())
    wb = lens_unfold((ckpts / "cold_b.ckpt").read_bytes())
    wb2 = lens_unfold((ckpts / "resume_b.ckpt").read_bytes())
    plan = [
        ("cold_a", fam_a, wa),
        ("resume_a", fam_a, wa2),
        ("cold_b", fam_b, wb),
        ("resume_b", fam_b, wb2),
        ("mix_c", mix_c, wa2),
        ("mix_d", mix_d, wb2),
    ]
    out = {}
    for sid, part, weights in plan:
        _n, edges, feats, labels = part
        out[sid] = score(feats, edges, labels, weights, agg, norm)
    return out


def main():
    req = json.loads(sys.stdin.read())
    data = Path(req.get("data", "/app/data"))
    cells = reference_cells(
        data,
        req["agg"],
        req["norm"],
        req["weft_c"],
        req["weft_d"],
    )
    print(json.dumps({k: [a, f] for k, (a, f) in cells.items()}))


if __name__ == "__main__":
    main()
