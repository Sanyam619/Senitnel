"""Shared fixture IO and IR metric helpers for the rerank evaluation desk."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Mark:
    idx: int
    state: str
    tip: str
    sheet: str
    weft_c: list[str] = field(default_factory=list)
    weft_d: list[str] = field(default_factory=list)


@dataclass
class Lot:
    name: str
    tags: list[int]
    lw: list[float]
    rows: list[list[float]]


def _field_at(line: str, key: str) -> str | None:
    pat = f'"{key}":'
    i = line.find(pat)
    if i < 0:
        return None
    return line[i + len(pat) :].lstrip()


def field_u32(line: str, key: str) -> int | None:
    rest = _field_at(line, key)
    if rest is None:
        return None
    end = 0
    while end < len(rest) and rest[end].isdigit():
        end += 1
    if end == 0:
        return None
    return int(rest[:end])


def field_str(line: str, key: str) -> str | None:
    rest = _field_at(line, key)
    if rest is None or not rest.startswith('"'):
        return None
    rest = rest[1:]
    end = rest.find('"')
    if end < 0:
        return None
    return rest[:end]


def field_list(line: str, key: str) -> list[str]:
    out: list[str] = []
    rest = _field_at(line, key)
    if rest is None or not rest.startswith("["):
        return out
    rest = rest[1:]
    end = rest.find("]")
    if end < 0:
        return out
    body = rest[:end]
    cur = body
    while True:
        q0 = cur.find('"')
        if q0 < 0:
            break
        after = cur[q0 + 1 :]
        q1 = after.find('"')
        if q1 < 0:
            break
        out.append(after[:q1])
        cur = after[q1 + 1 :]
    return out


def read_marks(path: Path) -> list[Mark]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out: list[Mark] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        idx = field_u32(line, "idx")
        if idx is None:
            continue
        out.append(
            Mark(
                idx=idx,
                state=field_str(line, "state") or "",
                tip=field_str(line, "tip") or "",
                sheet=field_str(line, "sheet") or "",
                weft_c=field_list(line, "weft_c"),
                weft_d=field_list(line, "weft_d"),
            )
        )
    return out


def rd_u32(b: bytes, off: list[int]) -> int:
    v = struct.unpack_from("<I", b, off[0])[0]
    off[0] += 4
    return v


def rd_u16(b: bytes, off: list[int]) -> int:
    v = struct.unpack_from("<H", b, off[0])[0]
    off[0] += 2
    return v


def rd_f32(b: bytes, off: list[int]) -> float:
    v = struct.unpack_from("<f", b, off[0])[0]
    off[0] += 4
    return float(v)


def rd_rowf(b: bytes, off: list[int], dim: int) -> list[float]:
    return [rd_f32(b, off) for _ in range(dim)]


def read_blob(path: Path) -> bytes:
    return path.read_bytes() if path.is_file() else b""


def read_lot(path: Path, name: str) -> Lot | None:
    b = read_blob(path)
    if len(b) < 12 or b[0:4] != b"SGB1":
        return None
    off = [4]
    n = rd_u32(b, off)
    dim = rd_u32(b, off)
    tags: list[int] = []
    lw: list[float] = []
    rows: list[list[float]] = []
    for _ in range(n):
        tags.append(rd_u16(b, off))
        lw.append(rd_f32(b, off))
        rows.append(rd_rowf(b, off, dim))
    return Lot(name=name, tags=tags, lw=lw, rows=rows)


def read_dir_lots(dir_path: Path, prefix: str) -> list[Lot]:
    if not dir_path.is_dir():
        return []
    names = sorted(n.name for n in dir_path.iterdir() if n.name.endswith(".bin"))
    out: list[Lot] = []
    for n in names:
        stem = n[: -len(".bin")]
        full = f"{prefix}/{stem}"
        lot = read_lot(dir_path / n, full)
        if lot is not None:
            out.append(lot)
    return out


def fold_all(lots: list[Lot], name: str) -> Lot:
    out = Lot(name=name, tags=[], lw=[], rows=[])
    for lot in lots:
        out.tags.extend(lot.tags)
        out.lw.extend(lot.lw)
        out.rows.extend(lot.rows)
    return out


def read_tags(blob: bytes) -> list[int]:
    if len(blob) < 12:
        return []
    magic = blob[0:4]
    off = [4]
    n = rd_u32(blob, off)
    _dim = rd_u32(blob, off)
    if magic == b"CKP2":
        _block = rd_u32(blob, off)
    elif magic != b"CKP1":
        return []
    return [rd_u16(blob, off) for _ in range(n)]


def braid_k(count: int, width: int) -> list[range]:
    out: list[range] = []
    if width == 0:
        if count > 0:
            out.append(range(count))
        return out
    start = 0
    while start < count:
        end = min(start + width, count)
        out.append(range(start, end))
        start = end
    return out


def d2(a: list[float], b: list[float]) -> float:
    s = 0.0
    for i in range(min(len(a), len(b))):
        d = float(a[i]) - float(b[i])
        s += d * d
    return s


def d2c(a: list[float], c: list[float]) -> float:
    s = 0.0
    for i in range(min(len(a), len(c))):
        d = float(a[i]) - float(c[i])
        s += d * d
    return s


def hits_at(qs: list[list[float]], qt: list[int], lot: Lot, tau: float, k: int) -> int:
    if not qs or not lot.rows:
        return 0
    hits = 0
    for span in braid_k(len(qs), 32):
        for qi in span:
            q = qs[qi]
            scored = [
                (-d2(q, row) + tau * float(lot.lw[ri]), ri)
                for ri, row in enumerate(lot.rows)
            ]
            scored.sort(key=lambda x: (-x[0], x[1]))
            top = scored[: min(k, len(scored))]
            if any(lot.tags[ri] == qt[qi] for _, ri in top):
                hits += 1
    return hits


def agree(qs: list[list[float]], qt: list[int], lot: Lot, tau: float) -> float:
    if not qs or not lot.rows:
        return 0.0
    dim = len(lot.rows[0])
    kinds = sorted(set(lot.tags))
    if len(kinds) < 2:
        return 0.0
    total = float(len(lot.rows))
    cores: list[list[float]] = []
    lp: list[float] = []
    for kind in kinds:
        acc = [0.0] * dim
        cnt = 0.0
        for ri, row in enumerate(lot.rows):
            if lot.tags[ri] == kind:
                for j, v in enumerate(row):
                    acc[j] += float(v)
                cnt += 1.0
        cores.append([v / cnt for v in acc])
        lp.append(math.log(cnt / total))
    asg: list[int] = []
    for q in qs:
        best = 0
        best_s = float("-inf")
        for ci, core in enumerate(cores):
            s = -d2c(q, core) + tau * lp[ci]
            if s > best_s:
                best_s = s
                best = ci
        asg.append(best)
    truth = sorted(set(qt))
    nq = float(len(qs))
    joint = [[0.0] * len(kinds) for _ in truth]
    for qi, a in enumerate(asg):
        ti = truth.index(qt[qi]) if qt[qi] in truth else 0
        joint[ti][a] += 1.0
    pt = [0.0] * len(truth)
    pa = [0.0] * len(kinds)
    for ti, row in enumerate(joint):
        for ai, c in enumerate(row):
            pt[ti] += c / nq
            pa[ai] += c / nq
    mi = 0.0
    for ti, row in enumerate(joint):
        for ai, c in enumerate(row):
            p = c / nq
            if p > 0.0 and pt[ti] > 0.0 and pa[ai] > 0.0:
                mi += p * math.log(p / (pt[ti] * pa[ai]))
    ht = sum(-p * math.log(p) for p in pt if p > 0.0)
    ha = sum(-p * math.log(p) for p in pa if p > 0.0)
    if ht <= 0.0 or ha <= 0.0:
        return 0.0
    return mi / math.sqrt(ht * ha)
