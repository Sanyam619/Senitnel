"""Caption-frame unfold for cold/resume query towers."""

from __future__ import annotations

import struct


def _rd_u32(b: bytes, off: list[int]) -> int:
    v = struct.unpack_from("<I", b, off[0])[0]
    off[0] += 4
    return v


def _rd_f32(b: bytes, off: list[int]) -> float:
    v = struct.unpack_from("<f", b, off[0])[0]
    off[0] += 4
    return float(v)


def _rd_rowf(b: bytes, off: list[int], dim: int) -> list[float]:
    return [_rd_f32(b, off) for _ in range(dim)]


def lens_unfold(blob: bytes) -> list[list[float]]:
    if len(blob) < 12:
        return []
    magic = blob[0:4]
    off = [4]
    n = _rd_u32(blob, off)
    dim = _rd_u32(blob, off)
    if magic == b"CKP1":
        off[0] += 2 * n
        return [_rd_rowf(blob, off, dim) for _ in range(n)]
    if magic == b"CKP2":
        block = _rd_u32(blob, off)
        off[0] += 2 * n
        out: list[list[float]] = []
        done = 0
        while done < n and block > 0:
            coef = _rd_f32(blob, off)
            take = min(block, n - done)
            for _ in range(take):
                row = _rd_rowf(blob, off, dim)
                if coef > 1.0:
                    row = [v * coef for v in row]
                out.append(row)
            done += take
        return out
    return []
