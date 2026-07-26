"""Shared fixture IO and contrastive VL metric helpers."""

from __future__ import annotations

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


def hits_at(
    qs: list[list[float]],
    qt: list[int],
    lot: Lot,
    tau: float,
    k: int,
    pool: str,
) -> int:
    if not qs or not lot.rows:
        return 0
    hard = pool == "hardmine"
    hits = 0
    for span in braid_k(len(qs), 32):
        for qi in span:
            q = qs[qi]
            scored = []
            for ri, row in enumerate(lot.rows):
                base = -d2(q, row)
                if hard:
                    base = base + tau * float(lot.lw[ri])
                scored.append((base, ri))
            scored.sort(key=lambda x: (-x[0], x[1]))
            top = scored[: min(k, len(scored))]
            if any(lot.tags[ri] == qt[qi] for _, ri in top):
                hits += 1
    return hits
