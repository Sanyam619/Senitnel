#!/usr/bin/env python3
"""One-shot generator for tasks/block-volume-crash-reconcile (authoring tool, not shipped)."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "block-volume-crash-reconcile"
TASK_ROOT = "/opt/kvfs"

BLOCK = 4096
TOTAL_BLOCKS = 256
MAGIC = b"KVFS"
VERSION = 1

INODE_TABLE_BLK = 2
INODE_TABLE_BLKS = 4
INODE_CAPACITY = 128
INODE_SIZE = 128
BITMAP_BLK = 6
BITMAP_BLKS = 2
JOURNAL_BLK = 8
JOURNAL_BLKS = 20
DATA_START = 28

TAG_PAD = 0x00
TAG_TX_OPEN = 0xA1
TAG_BLK_PATCH = 0xA2
TAG_TX_SEAL = 0xA3
TAG_BLK_FORGET = 0xA4

SCENARIOS = (
    "shard_a",
    "shard_b",
    "shard_c",
    "shard_d",
    "shard_e",
    "shard_f",
    "shard_g",
    "shard_h",
    "shard_i",
    "shard_j",
)


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def wbin(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def pack_super(
    *,
    epoch: int,
    durable_tx: int,
    primary_ok: int,
) -> bytes:
    body = struct.pack(
        "<4sIIIIIIIIIIIQQII",
        MAGIC,
        VERSION,
        BLOCK,
        TOTAL_BLOCKS,
        INODE_TABLE_BLK,
        INODE_TABLE_BLKS,
        INODE_CAPACITY,
        BITMAP_BLK,
        BITMAP_BLKS,
        JOURNAL_BLK,
        JOURNAL_BLKS,
        DATA_START,
        epoch,
        durable_tx,
        primary_ok,
        0,
    )
    csum = crc32(body[:-4])
    body = body[:-4] + struct.pack("<I", csum)
    return body.ljust(BLOCK, b"\x00")


def pack_inode(
    *,
    inode_id: int,
    mode: int,
    name: str,
    size: int,
    blocks: list[int],
    mtime: int = 1_700_000_000,
) -> bytes:
    direct = blocks + [0] * (12 - len(blocks))
    name_b = name.encode("utf-8")[:47]
    name_field = name_b.ljust(48, b"\x00")
    body = struct.pack("<HHII", mode, 1, size, inode_id)
    body += name_field
    body += struct.pack("<" + "H" * 12, *direct[:12])
    body += struct.pack("<Q", mtime)
    body += b"\x00" * (INODE_SIZE - len(body))
    return body[:INODE_SIZE]


def empty_image() -> bytearray:
    img = bytearray(BLOCK * TOTAL_BLOCKS)
    for blk in range(TOTAL_BLOCKS):
        img[blk * BLOCK : (blk + 1) * BLOCK] = b"\x00" * BLOCK
    return img


def write_block(img: bytearray, blk: int, data: bytes) -> None:
    chunk = data[:BLOCK].ljust(BLOCK, b"\x00")
    img[blk * BLOCK : (blk + 1) * BLOCK] = chunk


def write_inode(img: bytearray, inode_id: int, inode_bytes: bytes) -> None:
    idx = inode_id
    blk = INODE_TABLE_BLK + (idx * INODE_SIZE) // BLOCK
    off = (idx * INODE_SIZE) % BLOCK
    base = blk * BLOCK + off
    img[base : base + INODE_SIZE] = inode_bytes


def build_bitmap(used: set[int]) -> bytes:
    bits = bytearray(BITMAP_BLKS * BLOCK)
    for blk in used:
        if blk < TOTAL_BLOCKS:
            bits[blk // 8] |= 1 << (blk % 8)
    return bytes(bits)


def journal_offset(img: bytearray) -> int:
    base = JOURNAL_BLK * BLOCK
    end = (JOURNAL_BLK + JOURNAL_BLKS) * BLOCK
    pos = base
    while pos < end:
        tag = img[pos]
        if tag == TAG_PAD or tag == 0:
            return pos
        length = struct.unpack_from("<H", img, pos + 1)[0]
        pos += 3 + length
    return end - 3


def journal_append(img: bytearray, tag: int, body: bytes) -> None:
    pos = journal_offset(img)
    rec = bytes([tag]) + struct.pack("<H", len(body)) + body
    end = (JOURNAL_BLK + JOURNAL_BLKS) * BLOCK
    if pos + len(rec) > end:
        raise RuntimeError("journal full")
    img[pos : pos + len(rec)] = rec


def file_payload(text: str) -> bytes:
    return text.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replay_image(img: bytearray) -> dict:
    """Reference recovery used by oracle and golden generation."""

    def read_super(blk: int) -> dict:
        raw = bytes(img[blk * BLOCK : (blk + 1) * BLOCK])
        fields = struct.unpack_from("<4sIIIIIIIIIIIQQII", raw, 0)
        return {
            "magic": fields[0],
            "epoch": fields[12],
            "durable_tx": fields[13],
            "primary_ok": fields[14],
            "crc": fields[15],
        }

    s0, s1 = read_super(0), read_super(1)
    candidates = []
    for blk, sb in ((0, s0), (1, s1)):
        if sb["magic"] != MAGIC:
            continue
        body = img[blk * BLOCK : blk * BLOCK + 68]
        if crc32(body) != sb["crc"]:
            continue
        if sb["primary_ok"] != 1:
            continue
        candidates.append((sb["epoch"], sb["durable_tx"], blk))
    if not candidates:
        raise RuntimeError("no valid superblock")
    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    chosen_blk = candidates[0][2]

    base = JOURNAL_BLK * BLOCK
    end = (JOURNAL_BLK + JOURNAL_BLKS) * BLOCK

    def scan_journal() -> tuple[set[int], dict[int, list[tuple[int, bytes]]], list[tuple[int, list[int]]]]:
        pos = base
        sealed_local: set[int] = set()
        patches_local: dict[int, list[tuple[int, bytes]]] = {}
        forget_local: list[tuple[int, list[int]]] = []
        open_tx: int | None = None
        while pos < end:
            tag = img[pos]
            if tag in (TAG_PAD, 0):
                break
            length = struct.unpack_from("<H", img, pos + 1)[0]
            body = bytes(img[pos + 3 : pos + 3 + length])
            pos += 3 + length
            if tag == TAG_TX_OPEN:
                open_tx = struct.unpack_from("<Q", body, 0)[0]
                patches_local.setdefault(open_tx, [])
            elif tag == TAG_BLK_PATCH and open_tx is not None:
                blk_num = struct.unpack_from("<I", body, 0)[0]
                payload = body[4:]
                patches_local[open_tx].append((blk_num, payload))
            elif tag == TAG_TX_SEAL:
                tx_id = struct.unpack_from("<Q", body, 0)[0]
                sealed_local.add(tx_id)
                open_tx = None
            elif tag == TAG_BLK_FORGET:
                tx_id = struct.unpack_from("<Q", body, 0)[0]
                n = struct.unpack_from("<H", body, 8)[0]
                blocks = list(struct.unpack_from("<" + "I" * n, body, 10))
                forget_local.append((tx_id, blocks))
        return sealed_local, patches_local, forget_local

    sealed, tx_patches, forget_records = scan_journal()
    forget_suppress: dict[int, int] = {}
    for tx_id, blocks in forget_records:
        if tx_id not in sealed:
            continue
        for b in blocks:
            forget_suppress[b] = max(forget_suppress.get(b, 0), tx_id)

    work = bytearray(img)
    for tx_id in sorted(sealed):
        for blk_num, payload in tx_patches.get(tx_id, []):
            if blk_num in forget_suppress and forget_suppress[blk_num] > tx_id:
                continue
            write_block(work, blk_num, payload)

    inodes: dict[str, dict] = {}
    files: dict[str, str] = {}
    used_blocks: set[int] = set(range(DATA_START))

    for inode_id in range(INODE_CAPACITY):
        off = INODE_TABLE_BLK * BLOCK + inode_id * INODE_SIZE
        raw = bytes(work[off : off + INODE_SIZE])
        mode, _links, size, iid = struct.unpack_from("<HHII", raw, 0)
        if mode == 0:
            continue
        name = raw[12:60].split(b"\x00", 1)[0].decode("utf-8")
        direct = struct.unpack_from("<12H", raw, 60)
        block_list = [b for b in direct if b]
        used_blocks.update(block_list)
        inodes[name] = {
            "inode_id": int(iid),
            "mode": int(mode),
            "size": int(size),
            "blocks": block_list,
        }
        if mode == 1 and name.startswith("/"):
            chunks = []
            remain = size
            for b in block_list:
                if remain <= 0:
                    break
                chunk = bytes(work[b * BLOCK : b * BLOCK + min(BLOCK, remain)])
                chunks.append(chunk)
                remain -= BLOCK
            content = b"".join(chunks)[:size]
            files[name] = sha256_hex(content)

    bitmap = build_bitmap(used_blocks)
    return {
        "chosen_superblock": chosen_blk,
        "inodes": inodes,
        "bitmap_hex": bitmap.hex(),
        "files": files,
        "image": work,
    }


def inode_offset(inode_id: int) -> int:
    return INODE_TABLE_BLK * BLOCK + inode_id * INODE_SIZE


def inode_byte_offset(inode_id: int) -> tuple[int, int]:
    abs_off = inode_offset(inode_id)
    return abs_off // BLOCK, abs_off % BLOCK


def journal_patch_inode(scratch: bytearray, img: bytearray, inode_id: int, inode_bytes: bytes) -> None:
    blk, off = inode_byte_offset(inode_id)
    cur = bytearray(scratch[blk * BLOCK : (blk + 1) * BLOCK])
    cur[off : off + INODE_SIZE] = inode_bytes
    scratch[blk * BLOCK : (blk + 1) * BLOCK] = cur
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", blk) + bytes(cur))


def scenario_shard_a() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=10, durable_tx=2, primary_ok=1))
    write_block(img, 1, pack_super(epoch=9, durable_tx=2, primary_ok=1))

    notes_blk, cfg_blk = 40, 41
    write_block(img, notes_blk, file_payload("meeting at noon"))
    write_block(img, cfg_blk, file_payload("mode=prod"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/notes.txt", size=15, blocks=[notes_blk]))
    write_inode(img, 2, pack_inode(inode_id=2, mode=1, name="/config/app.cfg", size=9, blocks=[cfg_blk]))

    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), notes_blk, cfg_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 3, 2))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", notes_blk) + file_payload("meeting moved to 3pm"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/notes.txt", size=20, blocks=[notes_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 3))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 4, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", cfg_blk) + file_payload("mode=staging"))
    # tx 4 not sealed — crash

    golden = replay_image(img)
    stale = bytearray(img)
    write_inode(stale, 1, pack_inode(inode_id=1, mode=1, name="/notes.txt", size=15, blocks=[notes_blk]))
    write_block(stale, BITMAP_BLK, build_bitmap(used | {42}))
    return stale, golden


def scenario_shard_b() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=5, durable_tx=4, primary_ok=1))
    write_block(img, 1, pack_super(epoch=5, durable_tx=4, primary_ok=1))

    alpha_blk = 50
    beta_blk = 50
    write_block(img, alpha_blk, file_payload("ALPHA_V1"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/alpha.dat", size=8, blocks=[alpha_blk]))

    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), alpha_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 2, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", alpha_blk) + file_payload("ALPHA_V2"))
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 2))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 3, 4))
    journal_append(img, TAG_BLK_FORGET, struct.pack("<QH", 3, 1) + struct.pack("<I", alpha_blk))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", beta_blk) + file_payload("BETA"))
    scratch = bytearray(img)
    journal_patch_inode(scratch, img, 1, pack_inode(inode_id=1, mode=0, name="", size=0, blocks=[]))
    journal_patch_inode(
        scratch,
        img,
        2,
        pack_inode(inode_id=2, mode=1, name="/beta.dat", size=4, blocks=[beta_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 3))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 4, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", 51) + file_payload("GAMMA_PARTIAL"))
    # crash before seal

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, alpha_blk, file_payload("ALPHA_V1"))
    return corrupt, golden


def scenario_shard_c() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=17, durable_tx=4, primary_ok=1))
    write_block(img, 1, pack_super(epoch=17, durable_tx=4, primary_ok=1))

    ledger_blk, audit_blk = 60, 61
    write_block(img, ledger_blk, file_payload("row=100"))
    write_block(img, audit_blk, file_payload("row=200"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/ledger.tsv", size=7, blocks=[ledger_blk]))
    write_inode(img, 2, pack_inode(inode_id=2, mode=1, name="/audit.tsv", size=7, blocks=[audit_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), ledger_blk, audit_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 5, 2))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", ledger_blk) + file_payload("row=150"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/ledger.tsv", size=7, blocks=[ledger_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 5))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 6, 2))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", audit_blk) + file_payload("row=250"))
    journal_patch_inode(
        scratch,
        img,
        2,
        pack_inode(inode_id=2, mode=1, name="/audit.tsv", size=7, blocks=[audit_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 6))

    golden = replay_image(img)

    corrupt = bytearray(img)
    write_block(corrupt, 0, pack_super(epoch=20, durable_tx=5, primary_ok=1))
    write_block(corrupt, 1, pack_super(epoch=18, durable_tx=6, primary_ok=1))
    write_block(corrupt, ledger_blk, file_payload("row=100"))
    write_block(corrupt, audit_blk, file_payload("row=200"))
    return corrupt, golden


def scenario_shard_d() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=3, durable_tx=1, primary_ok=1))
    write_block(img, 1, pack_super(epoch=3, durable_tx=1, primary_ok=1))

    cache_blk = 70
    write_block(img, cache_blk, file_payload("v1"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/cache.bin", size=2, blocks=[cache_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), cache_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 2, 3))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", cache_blk) + file_payload("v2"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/cache.bin", size=2, blocks=[cache_blk]),
    )
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", 71) + file_payload("scratch"))
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 2))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 3, 1))
    journal_append(img, TAG_BLK_FORGET, struct.pack("<QH", 3, 1) + struct.pack("<I", 71))
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 3))

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, BITMAP_BLK, build_bitmap(used | {71, 72}))
    write_block(corrupt, cache_blk, file_payload("v1"))
    return corrupt, golden


def scenario_shard_e() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=8, durable_tx=3, primary_ok=1))
    write_block(img, 1, pack_super(epoch=25, durable_tx=10, primary_ok=0))

    arch_blk = 82
    write_block(img, arch_blk, file_payload("zip_v1"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/archive.zip", size=6, blocks=[arch_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), arch_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 4, 2))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", arch_blk) + file_payload("zip_v2"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/archive.zip", size=6, blocks=[arch_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 4))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 5, 2))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", 83) + file_payload("scratch"))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", BITMAP_BLK) + build_bitmap(used | {83, 84}))
    # tx 5 not sealed — crash

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, arch_blk, file_payload("zip_v1"))
    write_block(corrupt, BITMAP_BLK, build_bitmap(used | {83, 84}))
    return corrupt, golden


def scenario_shard_f() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=4, durable_tx=2, primary_ok=1))
    write_block(img, 1, pack_super(epoch=4, durable_tx=2, primary_ok=1))

    data_blk = 90
    write_block(img, data_blk, file_payload("v1"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/order.dat", size=2, blocks=[data_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), data_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 5, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", data_blk) + file_payload("v5"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/order.dat", size=2, blocks=[data_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 5))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 3, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", data_blk) + file_payload("v3"))
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/order.dat", size=2, blocks=[data_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 3))

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, data_blk, file_payload("v1"))
    return corrupt, golden


def scenario_shard_g() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=11, durable_tx=3, primary_ok=1))
    write_block(img, 1, pack_super(epoch=11, durable_tx=3, primary_ok=1))

    hold_blk = 95
    write_block(img, hold_blk, file_payload("baseline"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/hold.dat", size=8, blocks=[hold_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), hold_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 2, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", hold_blk) + file_payload("stable"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/hold.dat", size=6, blocks=[hold_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 2))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 3, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", hold_blk) + file_payload("volatile"))
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/hold.dat", size=8, blocks=[hold_blk]),
    )
    # tx 3 not sealed — crash

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, hold_blk, file_payload("baseline"))
    write_inode(corrupt, 1, pack_inode(inode_id=1, mode=1, name="/hold.dat", size=8, blocks=[hold_blk]))
    return corrupt, golden


def scenario_shard_h() -> tuple[bytearray, dict]:
    img = empty_image()
    write_block(img, 0, pack_super(epoch=7, durable_tx=5, primary_ok=1))
    write_block(img, 1, pack_super(epoch=7, durable_tx=5, primary_ok=1))

    layer_blk = 102
    write_block(img, layer_blk, file_payload("baseline"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/layer.dat", size=8, blocks=[layer_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), layer_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 9, 2))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", layer_blk) + file_payload("first"))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", layer_blk) + file_payload("second"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/layer.dat", size=6, blocks=[layer_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 9))

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, layer_blk, file_payload("baseline"))
    return corrupt, golden


def scenario_shard_i() -> tuple[bytearray, dict]:
    """Header durable_tx lags sealed journal work — watermark clipping must not drop later seals."""
    img = empty_image()
    write_block(img, 0, pack_super(epoch=9, durable_tx=2, primary_ok=1))
    write_block(img, 1, pack_super(epoch=9, durable_tx=2, primary_ok=1))

    lag_blk = 110
    write_block(img, lag_blk, file_payload("seed"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/lag.dat", size=4, blocks=[lag_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), lag_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 2, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", lag_blk) + file_payload("mid"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/lag.dat", size=3, blocks=[lag_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 2))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 7, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", lag_blk) + file_payload("ahead"))
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/lag.dat", size=5, blocks=[lag_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 7))

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, lag_blk, file_payload("seed"))
    write_inode(corrupt, 1, pack_inode(inode_id=1, mode=1, name="/lag.dat", size=4, blocks=[lag_blk]))
    return corrupt, golden


def scenario_shard_j() -> tuple[bytearray, dict]:
    """Unsealed BLK_FORGET must not suppress an earlier sealed payload."""
    img = empty_image()
    write_block(img, 0, pack_super(epoch=6, durable_tx=4, primary_ok=1))
    write_block(img, 1, pack_super(epoch=6, durable_tx=4, primary_ok=1))

    keep_blk = 118
    write_block(img, keep_blk, file_payload("OLD"))

    write_inode(img, 1, pack_inode(inode_id=1, mode=1, name="/keep.dat", size=3, blocks=[keep_blk]))
    used = {0, 1, 2, 3, 4, 5, 6, 7, *range(8, 28), keep_blk}
    write_block(img, BITMAP_BLK, build_bitmap(used))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 4, 1))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", keep_blk) + file_payload("KEEP"))
    scratch = bytearray(img)
    journal_patch_inode(
        scratch,
        img,
        1,
        pack_inode(inode_id=1, mode=1, name="/keep.dat", size=4, blocks=[keep_blk]),
    )
    journal_append(img, TAG_TX_SEAL, struct.pack("<Q", 4))

    journal_append(img, TAG_TX_OPEN, struct.pack("<QH", 8, 2))
    journal_append(img, TAG_BLK_FORGET, struct.pack("<QH", 8, 1) + struct.pack("<I", keep_blk))
    journal_append(img, TAG_BLK_PATCH, struct.pack("<I", keep_blk) + file_payload("DROP"))
    # crash before seal — forget and DROP must not apply

    golden = replay_image(img)
    corrupt = bytearray(img)
    write_block(corrupt, keep_blk, file_payload("OLD"))
    write_inode(corrupt, 1, pack_inode(inode_id=1, mode=1, name="/keep.dat", size=3, blocks=[keep_blk]))
    return corrupt, golden


BUILDERS = {
    "shard_a": scenario_shard_a,
    "shard_b": scenario_shard_b,
    "shard_c": scenario_shard_c,
    "shard_d": scenario_shard_d,
    "shard_e": scenario_shard_e,
    "shard_f": scenario_shard_f,
    "shard_g": scenario_shard_g,
    "shard_h": scenario_shard_h,
    "shard_i": scenario_shard_i,
    "shard_j": scenario_shard_j,
}


def golden_blob() -> dict:
    out: dict[str, dict] = {}
    for name, fn in BUILDERS.items():
        _img, golden = fn()
        out[name] = {
            "chosen_superblock": golden["chosen_superblock"],
            "inode_count": len(golden["inodes"]),
            "bitmap_hex": golden["bitmap_hex"],
            "files": golden["files"],
            "inode_paths": sorted(golden["inodes"].keys()),
        }
    return out


def emit_tests() -> str:
    return f'''import json
import subprocess
from pathlib import Path

SCENARIOS = {json.dumps(list(SCENARIOS))}
BLOCK = {BLOCK}
TOTAL_BLOCKS = {TOTAL_BLOCKS}
INODE_TABLE_BLK = {INODE_TABLE_BLK}
INODE_CAPACITY = {INODE_CAPACITY}
INODE_SIZE = {INODE_SIZE}
BITMAP_BLK = {BITMAP_BLK}
BITMAP_BLKS = {BITMAP_BLKS}
JOURNAL_BLK = {JOURNAL_BLK}
JOURNAL_BLKS = {JOURNAL_BLKS}
DATA_START = {DATA_START}
MAGIC = b"KVFS"
TAG_PAD = {TAG_PAD}
TAG_TX_OPEN = {TAG_TX_OPEN}
TAG_BLK_PATCH = {TAG_BLK_PATCH}
TAG_TX_SEAL = {TAG_TX_SEAL}
TAG_BLK_FORGET = {TAG_BLK_FORGET}
DATA = Path("{TASK_ROOT}/data/scenarios")
OUT = Path("/output")


def _crc32(data: bytes) -> int:
    poly = 0xEDB88320
    state = 0xFFFFFFFF
    for byte in data:
        state ^= byte
        for _ in range(8):
            state = (state >> 1) ^ poly if state & 1 else state >> 1
    return (~state) & 0xFFFFFFFF


def _sha256_hex(data: bytes) -> str:
    proc = subprocess.run(
        ["sha256sum"],
        input=data,
        capture_output=True,
        check=True,
        text=False,
    )
    return proc.stdout.decode().split()[0]


def _write_block(img: bytearray, blk: int, data: bytes) -> None:
    chunk = data[:BLOCK].ljust(BLOCK, b"\\x00")
    img[blk * BLOCK : (blk + 1) * BLOCK] = chunk


def _build_bitmap(used: set[int]) -> bytes:
    bits = bytearray(BITMAP_BLKS * BLOCK)
    for blk in used:
        if blk < TOTAL_BLOCKS:
            bits[blk // 8] |= 1 << (blk % 8)
    return bytes(bits)


def _reconcile(path: Path) -> tuple[bytearray, dict]:
    img = bytearray(path.read_bytes())

    def read_super(blk: int) -> tuple[bytes, int, int, int, int]:
        raw = bytes(img[blk * BLOCK : (blk + 1) * BLOCK])
        magic = raw[0:4]
        epoch = int.from_bytes(raw[48:56], "little")
        durable_tx = int.from_bytes(raw[56:64], "little")
        primary_ok = int.from_bytes(raw[64:68], "little")
        crc = int.from_bytes(raw[68:72], "little")
        return magic, epoch, durable_tx, primary_ok, crc

    candidates = []
    for blk in (0, 1):
        magic, epoch, durable_tx, primary_ok, crc = read_super(blk)
        if magic != MAGIC:
            continue
        body = img[blk * BLOCK : blk * BLOCK + 68]
        if _crc32(body) != crc or primary_ok != 1:
            continue
        candidates.append((epoch, durable_tx, blk))
    chosen_blk = max(candidates, key=lambda item: (item[0], item[1], -item[2]))[2]

    base = JOURNAL_BLK * BLOCK
    end = (JOURNAL_BLK + JOURNAL_BLKS) * BLOCK
    pos = base
    sealed: set[int] = set()
    patches: dict[int, list[tuple[int, bytes]]] = {{}}
    forget_records: list[tuple[int, list[int]]] = []
    open_tx = None
    while pos < end:
        tag = img[pos]
        if tag in (TAG_PAD, 0):
            break
        length = int.from_bytes(img[pos + 1 : pos + 3], "little")
        body = bytes(img[pos + 3 : pos + 3 + length])
        pos += 3 + length
        if tag == TAG_TX_OPEN:
            open_tx = int.from_bytes(body[0:8], "little")
            patches.setdefault(open_tx, [])
        elif tag == TAG_BLK_PATCH and open_tx is not None:
            blk_num = int.from_bytes(body[0:4], "little")
            patches[open_tx].append((blk_num, body[4:]))
        elif tag == TAG_TX_SEAL:
            sealed.add(int.from_bytes(body[0:8], "little"))
            open_tx = None
        elif tag == TAG_BLK_FORGET:
            tx_id = int.from_bytes(body[0:8], "little")
            n = int.from_bytes(body[8:10], "little")
            blocks = [int.from_bytes(body[10 + 4 * i : 14 + 4 * i], "little") for i in range(n)]
            forget_records.append((tx_id, blocks))

    forget_suppress: dict[int, int] = {{}}
    for tx_id, blocks in forget_records:
        if tx_id not in sealed:
            continue
        for blk in blocks:
            forget_suppress[blk] = max(forget_suppress.get(blk, 0), tx_id)

    work = bytearray(img)
    for tx_id in sorted(sealed):
        for blk_num, payload in patches.get(tx_id, []):
            if blk_num in forget_suppress and forget_suppress[blk_num] > tx_id:
                continue
            _write_block(work, blk_num, payload)

    files: dict[str, str] = {{}}
    used_blocks: set[int] = set(range(DATA_START))
    for inode_id in range(INODE_CAPACITY):
        off = INODE_TABLE_BLK * BLOCK + inode_id * INODE_SIZE
        raw = bytes(work[off : off + INODE_SIZE])
        mode = int.from_bytes(raw[0:2], "little")
        size = int.from_bytes(raw[4:8], "little")
        if mode != 1:
            continue
        name = raw[12:60].split(b"\\x00", 1)[0].decode("utf-8")
        direct = [int.from_bytes(raw[60 + 2 * i : 62 + 2 * i], "little") for i in range(12)]
        block_list = [b for b in direct if b]
        used_blocks.update(block_list)
        chunks = []
        remain = size
        for blk in block_list:
            if remain <= 0:
                break
            chunk = bytes(work[blk * BLOCK : blk * BLOCK + min(BLOCK, remain)])
            chunks.append(chunk)
            remain -= BLOCK
        content = b"".join(chunks)[:size]
        if name.startswith("/"):
            files[name] = _sha256_hex(content)

    bitmap = _build_bitmap(used_blocks)
    work[BITMAP_BLK * BLOCK : BITMAP_BLK * BLOCK + len(bitmap)] = bitmap

    meta = {{
        "chosen_superblock": chosen_blk,
        "files": files,
        "bitmap_hex": bitmap.hex(),
    }}
    return work, meta


def _reference_view(path: Path) -> dict:
    _, meta = _reconcile(path)
    return meta


def _reconcile_work(path: Path) -> bytearray:
    work, _ = _reconcile(path)
    return work


def _files_from_image_bytes(work: bytes | bytearray) -> dict[str, str]:
    files: dict[str, str] = {{}}
    for inode_id in range(INODE_CAPACITY):
        off = INODE_TABLE_BLK * BLOCK + inode_id * INODE_SIZE
        raw = bytes(work[off : off + INODE_SIZE])
        mode = int.from_bytes(raw[0:2], "little")
        size = int.from_bytes(raw[4:8], "little")
        if mode != 1:
            continue
        name = raw[12:60].split(b"\\x00", 1)[0].decode("utf-8")
        direct = [int.from_bytes(raw[60 + 2 * i : 62 + 2 * i], "little") for i in range(12)]
        block_list = [b for b in direct if b]
        chunks = []
        remain = size
        for blk in block_list:
            if remain <= 0:
                break
            chunk = bytes(work[blk * BLOCK : blk * BLOCK + min(BLOCK, remain)])
            chunks.append(chunk)
            remain -= BLOCK
        content = b"".join(chunks)[:size]
        if name.startswith("/"):
            files[name] = _sha256_hex(content)
    return files


def _load_report() -> dict:
    path = OUT / "recovered_state.json"
    assert path.is_file(), "missing /output/recovered_state.json"
    return json.loads(path.read_text())


def test_report_top_level():
    """Recovery report names every bundled scenario shard."""
    report = _load_report()
    assert "scenarios" in report
    for name in SCENARIOS:
        assert name in report["scenarios"], f"missing scenario {{name}}"


def test_report_matches_scenario_directory():
    """Recovery report lists exactly the scenario basenames shipped under the data directory."""
    report = _load_report()
    on_disk = sorted(p.stem for p in DATA.glob("*.img"))
    assert sorted(report["scenarios"].keys()) == on_disk


def _sha256_file(path: Path) -> str:
    proc = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        check=True,
        text=True,
    )
    return proc.stdout.split()[0]


def test_scenario_inputs_unchanged():
    """Bundled scenario images under the read-only data directory are left unmodified."""
    manifest = json.loads((DATA.parent / "scenario_manifest.json").read_text())
    for name, digest in manifest.items():
        assert _sha256_file(DATA / f"{{name}}.img") == digest


def test_volpeek_binary_unchanged():
    """The bundled inspector binary is not rebuilt or replaced."""
    expected = Path("{TASK_ROOT}/packaging/volpeek.sha256").read_text().strip()
    assert _sha256_file(Path("{TASK_ROOT}/bin/volpeek")) == expected


def test_rebuilt_images_exist():
    """Each scenario has a matching rebuilt raw image on disk."""
    for name in SCENARIOS:
        path = OUT / f"rebuilt_{{name}}.img"
        assert path.is_file(), f"missing rebuilt image for {{name}}"
        assert path.stat().st_size == BLOCK * TOTAL_BLOCKS


def test_rebuilt_images_match_reconciled_layout():
    """Rebuilt raw images match the reconciled allocation map and patched block payloads."""
    for name in SCENARIOS:
        expected = _reconcile_work(DATA / f"{{name}}.img")
        rebuilt = (OUT / f"rebuilt_{{name}}.img").read_bytes()
        assert rebuilt == bytes(expected)


def test_all_scenarios_report_complete_fields():
    """Every shard reports header choice, reconciled file digests, and allocation map."""
    report = _load_report()
    for name in SCENARIOS:
        entry = report["scenarios"][name]
        assert entry["chosen_superblock"] in (0, 1)
        assert isinstance(entry["files"], dict)
        assert isinstance(entry["bitmap_hex"], str) and entry["bitmap_hex"]
        expected = _reference_view(DATA / f"{{name}}.img")
        assert entry["chosen_superblock"] == expected["chosen_superblock"]
        assert entry["bitmap_hex"] == expected["bitmap_hex"]
        assert entry["files"] == expected["files"]


def test_rebuilt_images_carry_report_file_payloads():
    """Rebuilt images expose the same live file payloads named in the recovery report."""
    report = _load_report()
    for name in SCENARIOS:
        files = _files_from_image_bytes((OUT / f"rebuilt_{{name}}.img").read_bytes())
        assert files == report["scenarios"][name]["files"]


def test_shard_a_file_digests():
    """Primary shard restores updated note content and stable config payload."""
    expected = _reference_view(DATA / "shard_a.img")
    report = _load_report()["scenarios"]["shard_a"]
    assert report["files"]["/notes.txt"] == expected["files"]["/notes.txt"]
    assert report["files"]["/config/app.cfg"] == expected["files"]["/config/app.cfg"]


def test_shard_b_forget_suppression():
    """Reuse shard keeps beta payload when an older patch targeted the same physical block."""
    expected = _reference_view(DATA / "shard_b.img")
    report = _load_report()["scenarios"]["shard_b"]
    assert "/alpha.dat" not in report["files"]
    assert report["files"]["/beta.dat"] == expected["files"]["/beta.dat"]


def test_shard_c_header_choice():
    """Disagreeing redundant headers resolve to the durable generation with later sealed work."""
    expected = _reference_view(DATA / "shard_c.img")
    report = _load_report()["scenarios"]["shard_c"]
    assert report["chosen_superblock"] == expected["chosen_superblock"]
    assert report["files"]["/ledger.tsv"] == expected["files"]["/ledger.tsv"]
    assert report["files"]["/audit.tsv"] == expected["files"]["/audit.tsv"]


def test_shard_d_bitmap_consistency():
    """Rebuilt free list matches inode-derived allocation after sealed work only."""
    expected = _reference_view(DATA / "shard_d.img")
    report = _load_report()["scenarios"]["shard_d"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]
    assert report["files"]["/cache.bin"] == expected["files"]["/cache.bin"]


def test_shard_e_invalid_header_decoy():
    """A newer-looking redundant header with primary_ok cleared must not win selection."""
    expected = _reference_view(DATA / "shard_e.img")
    report = _load_report()["scenarios"]["shard_e"]
    assert report["chosen_superblock"] == expected["chosen_superblock"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]
    assert report["files"]["/archive.zip"] == expected["files"]["/archive.zip"]


def test_shard_f_out_of_band_tx_order():
    """Sealed work from a higher tx_id logged after an earlier id still wins after reconciliation."""
    expected = _reference_view(DATA / "shard_f.img")
    report = _load_report()["scenarios"]["shard_f"]
    assert report["files"]["/order.dat"] == expected["files"]["/order.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_g_unsealed_tx_ignored():
    """A crash-interrupted transaction must not overwrite durable sealed payload on the same block."""
    expected = _reference_view(DATA / "shard_g.img")
    report = _load_report()["scenarios"]["shard_g"]
    assert report["files"]["/hold.dat"] == expected["files"]["/hold.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_h_intra_tx_patch_order():
    """When one sealed transaction patches the same data block twice, the later journal patch wins."""
    expected = _reference_view(DATA / "shard_h.img")
    report = _load_report()["scenarios"]["shard_h"]
    assert report["files"]["/layer.dat"] == expected["files"]["/layer.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_i_durable_tx_lag():
    """Sealed redo beyond the chosen header durable_tx watermark must still land in the rebuilt image."""
    expected = _reference_view(DATA / "shard_i.img")
    report = _load_report()["scenarios"]["shard_i"]
    assert report["files"]["/lag.dat"] == expected["files"]["/lag.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_j_unsealed_forget_ignored():
    """An unsealed BLK_FORGET must not erase a previously sealed payload on the same block."""
    expected = _reference_view(DATA / "shard_j.img")
    report = _load_report()["scenarios"]["shard_j"]
    assert report["files"]["/keep.dat"] == expected["files"]["/keep.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_volpeek_runs_on_scenario_inputs():
    """Bundled inspector runs cleanly against each scenario image."""
    for name in SCENARIOS:
        proc = subprocess.run(
            ["{TASK_ROOT}/bin/volpeek", str(DATA / f"{{name}}.img")],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert "chosen_superblock=" in proc.stdout


def test_shard_a_live_paths():
    """Primary shard recovery report lists every reconciled live path."""
    expected = _reference_view(DATA / "shard_a.img")
    report = _load_report()["scenarios"]["shard_a"]
    assert sorted(report["files"].keys()) == sorted(expected["files"].keys())


def test_cross_scenario_inode_counts():
    """Each scenario exposes the expected number of live paths after reconciliation."""
    report = _load_report()
    for name in SCENARIOS:
        expected = _reference_view(DATA / f"{{name}}.img")
        live = len(report["scenarios"][name]["files"])
        assert live == len(expected["files"])
'''


def emit_solve_sh() -> str:
    return f"""#!/bin/bash
set -euo pipefail

mkdir -p /output
cd {TASK_ROOT}

cat > ops/apply_site_policy.sh <<'APPLYEOF'
#!/bin/bash
set -euo pipefail

POLICY="/opt/kvfs/config/recovery_policy.ini"
BACKUP="${{POLICY}}.pre-kvfs441"
STAMP="/opt/kvfs/config/.policy_refresh.stamp"
LOG_PREFIX="[kvfs-site-policy]"

log() {{
  echo "$LOG_PREFIX $*"
}}

require_config_dir() {{
  if [[ ! -d /opt/kvfs/config ]]; then
    log "config directory missing"
    exit 1
  fi
}}

backup_current_policy() {{
  if [[ -f "$POLICY" ]]; then
    cp -a "$POLICY" "$BACKUP"
    log "saved prior policy to $(basename "$BACKUP")"
  fi
}}

write_policy_bundle() {{
  cat > "$POLICY" <<'EOF'
# KVFS batch recovery policy — site standard after crash review
[replay]
order=tx_id
forget_mode=invalidate_earlier

[bitmap]
metadata_used_end=28

[image]
patch_zero_pad=1
preserve_superblocks=1

[header]
prefer=epoch
EOF
}}

stamp_refresh() {{
  date -u +%Y-%m-%dT%H:%M:%SZ > "$STAMP"
  log "policy refresh stamped"
}}

require_config_dir
backup_current_policy
write_policy_bundle
stamp_refresh
log "site policy bundle applied"
APPLYEOF
chmod +x ops/apply_site_policy.sh

cat > ops/run_recovery.sh <<'RUNEOF'
#!/bin/bash
set -euo pipefail
cd /opt/kvfs
if [[ ! -x ops/apply_site_policy.sh ]]; then
  echo "missing apply_site_policy.sh" >&2
  exit 1
fi
./ops/apply_site_policy.sh
if [[ ! -f config/recovery_policy.ini ]]; then
  echo "policy missing after apply" >&2
  exit 1
fi
rm -f bin/reconcile lib/m3_apply.o lib/p7_sb.o
make bin/reconcile
mkdir -p /output
bin/reconcile
RUNEOF
chmod +x ops/run_recovery.sh

cp /solution/patch/m3_apply.c lib/m3_apply.c
cp /solution/patch/reconcile.c tools/reconcile.c
cp /solution/patch/p7_sb.c lib/p7_sb.c

ops/run_recovery.sh
"""


def main() -> None:
    if TASK.exists():
        import shutil

        shutil.rmtree(TASK)

    gold = golden_blob()

    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "system-administration"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["c"]
tags = ["filesystem", "crash-recovery", "block-device", "c", "data-integrity"]
expert_time_estimate_min = 90
junior_time_estimate_min = 300

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
""",
    )

    rebuilt_list = ", ".join(f"`/output/rebuilt_{name}.img`" for name in SCENARIOS)
    w(
        TASK / "instruction.md",
        f"""After an unclean shutdown, operations copied ten KVFS block-volume images into `{TASK_ROOT}/data/scenarios/`. Each image is an independent crash story — field notes in `{TASK_ROOT}/docs/scenario_notes.md` describe what operators observed when they tried to read files back. Symptoms overlap: stale file bytes, allocation-map drift, disagreeing redundant headers, and batch recovery that exits cleanly yet leaves shards wrong.

On-disk layout and reconciliation semantics live in `{TASK_ROOT}/docs/vol_format.md`. A read-only inspector is at `{TASK_ROOT}/bin/volpeek`. The site recovery toolchain under `{TASK_ROOT}` (start from `{TASK_ROOT}/ops/run_recovery.sh`; inspect `{TASK_ROOT}/config/`, `{TASK_ROOT}/lib/`, `{TASK_ROOT}/tools/`) produced the last bad batch — see `{TASK_ROOT}/ops/recovery_status.txt`. Restore a consistent view for every scenario image and write the outputs below.

For every basename in `{TASK_ROOT}/data/scenarios/` (without `.img`), emit `/output/recovered_state.json` with a top-level `scenarios` object: each entry needs integer `chosen_superblock` (0 or 1), `files` mapping absolute paths to lowercase hex SHA-256 digests, and `bitmap_hex` as contiguous hex over the full allocation-map region. Also write {rebuilt_list} — full raw images matching input byte length whose inode table, allocation map, and file payloads reflect the reconciled state. Do not modify inputs under `{TASK_ROOT}/data/scenarios/`. Do not rebuild or replace `{TASK_ROOT}/bin/volpeek`; it must stay byte-identical to `{TASK_ROOT}/packaging/volpeek.sha256`.
""",
    )

    rebuilt_outputs = ",\n  ".join(f'"/output/rebuilt_{name}.img"' for name in SCENARIOS)
    w(
        TASK / "output_contract.toml",
        f"""user_visible_outputs = [
  "/output/recovered_state.json",
  {rebuilt_outputs},
]

internal_harness_files = [
  "/tests/test_outputs.py",
]

[structured_outputs.recovered_state]
target = "/output/recovered_state.json"
format = "json"
instruction_checks = [
  "scenarios",
  "chosen_superblock",
  "files",
  "bitmap_hex",
]
""",
    )

    w(
        TASK / "environment" / "Dockerfile",
        f"""# syntax=docker/dockerfile:1

# Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema=2.2.0-1 \\
        tmux=3.3a-3 \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash \\
        ca-certificates \\
        coreutils \\
        libssl-dev \\
        procps \\
        python3 \\
        python3-pip \\
        zlib1g-dev \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY include {TASK_ROOT}/include
COPY lib {TASK_ROOT}/lib
COPY tools {TASK_ROOT}/tools
COPY docs {TASK_ROOT}/docs
COPY data {TASK_ROOT}/data
COPY config {TASK_ROOT}/config
COPY Makefile {TASK_ROOT}/Makefile
COPY ops {TASK_ROOT}/ops
COPY packaging {TASK_ROOT}/packaging

RUN make -C {TASK_ROOT} clean bin/volpeek \\
    && sha256sum {TASK_ROOT}/bin/volpeek | awk '{{print $1}}' > {TASK_ROOT}/packaging/volpeek.sha256 \\
    && chmod +x {TASK_ROOT}/ops/*.sh

WORKDIR {TASK_ROOT}
ENV PATH="{TASK_ROOT}/bin:${{PATH}}"
""",
    )

    w(
        TASK / "environment" / ".dockerignore",
        """.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/.mypy_cache/
**/.ruff_cache/
**/node_modules/
**/target/
**/dist/
**/build/
**/.venv/
**/venv/
.env
*.log
*.o
*.a
bin/
lib/*.o
tools/*.o
solution/
tests/
""",
    )

    w(
        TASK / "environment" / "Makefile",
        f"""CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -I{TASK_ROOT}/include -I{TASK_ROOT}/lib
LDFLAGS = -lz
RECON_LDFLAGS = -lz -lcrypto -lssl

LIB_SRCS = lib/k9_scan.c lib/m3_apply.c lib/p7_sb.c lib/r2_inode.c lib/u8_crc.c
LIB_OBJS = $(LIB_SRCS:.c=.o)
TOOL_SRCS = tools/volpeek.c
TOOL_OBJS = $(TOOL_SRCS:.c=.o)

.PHONY: all clean

all: bin/volpeek bin/reconcile lib/libkvfs.a

bin:
\tmkdir -p bin

bin/reconcile: bin tools/reconcile.c lib/libkvfs.a lib/m3_apply.o
\t$(CC) $(CFLAGS) -o $@ tools/reconcile.c lib/m3_apply.o lib/libkvfs.a $(RECON_LDFLAGS)

lib/m3_apply.o: lib/m3_apply.c
\t$(CC) $(CFLAGS) -c -o $@ lib/m3_apply.c

lib/libkvfs.a: $(LIB_OBJS)
\tar rcs $@ $(LIB_OBJS)

bin/volpeek: bin $(TOOL_OBJS) lib/libkvfs.a
\t$(CC) $(CFLAGS) -o $@ $(TOOL_OBJS) lib/libkvfs.a $(LDFLAGS)

%.o: %.c
\t$(CC) $(CFLAGS) -c -o $@ $<

clean:
\trm -f lib/*.o tools/*.o bin/volpeek bin/reconcile lib/libkvfs.a
""",
    )

    w(
        TASK / "environment" / "include" / "kvfs_layout.h",
        f"""#ifndef KVFS_LAYOUT_H
#define KVFS_LAYOUT_H

#include <stdint.h>

#define KVFS_MAGIC "KVFS"
#define KVFS_VERSION 1
#define KVFS_BLOCK_SIZE {BLOCK}
#define KVFS_TOTAL_BLOCKS {TOTAL_BLOCKS}

#define KVFS_INODE_TABLE_BLK {INODE_TABLE_BLK}
#define KVFS_INODE_TABLE_BLKS {INODE_TABLE_BLKS}
#define KVFS_INODE_CAPACITY {INODE_CAPACITY}
#define KVFS_INODE_SIZE {INODE_SIZE}

#define KVFS_BITMAP_BLK {BITMAP_BLK}
#define KVFS_BITMAP_BLKS {BITMAP_BLKS}

#define KVFS_JOURNAL_BLK {JOURNAL_BLK}
#define KVFS_JOURNAL_BLKS {JOURNAL_BLKS}

#define KVFS_DATA_START {DATA_START}

#define KVFS_TAG_PAD 0x00
#define KVFS_TAG_TX_OPEN 0xA1
#define KVFS_TAG_BLK_PATCH 0xA2
#define KVFS_TAG_TX_SEAL 0xA3
#define KVFS_TAG_BLK_FORGET 0xA4

#pragma pack(push, 1)
typedef struct {{
    char magic[4];
    uint32_t version;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t inode_table_blk;
    uint32_t inode_table_blks;
    uint32_t inode_capacity;
    uint32_t bitmap_blk;
    uint32_t bitmap_blks;
    uint32_t journal_blk;
    uint32_t journal_blks;
    uint32_t data_start_blk;
    uint64_t epoch;
    uint64_t durable_tx;
    uint32_t primary_ok;
    uint32_t sb_crc32;
}} kvfs_super_t;

typedef struct {{
    uint16_t mode;
    uint16_t links;
    uint32_t size;
    uint32_t inode_id;
    char name[48];
    uint16_t direct[12];
    uint64_t mtime;
    uint8_t pad[24];
}} kvfs_inode_t;
#pragma pack(pop)

#endif
""",
    )

    w(
        TASK / "environment" / "include" / "kvfs_api.h",
        """#ifndef KVFS_API_H
#define KVFS_API_H

#include <stddef.h>
#include <stdint.h>

typedef struct kvfs_volume kvfs_volume;

kvfs_volume *op_open_vol(const char *path);
void op_close_vol(kvfs_volume *vol);
int op_read_block(kvfs_volume *vol, uint32_t blk, void *out, size_t len);
int step_a_scan_redo(kvfs_volume *vol, uint64_t *tx_count);
int resolve_c_pick_header(kvfs_volume *vol, uint32_t *chosen_blk);
int r2_walk_inodes(kvfs_volume *vol, void (*cb)(const char *name, uint32_t size, void *ctx), void *ctx);
uint32_t u8_crc32_bytes(const void *data, size_t len);

#endif
""",
    )

    w(
        TASK / "environment" / "docs" / "vol_format.md",
        """# KVFS on-disk layout

KVFS stores a fixed 4096-byte block array. Blocks 0 and 1 are redundant volume headers (`kvfs_super_t`). The inode table begins at block 2 and spans four blocks. Each inode is 128 bytes. Mode 0 means unused; mode 1 is a regular file. The `name` field stores an absolute path. `direct[]` lists data block indices.

The allocation map occupies blocks 6–7 as a bit vector indexed by block number.

The circular redo area occupies blocks 8–27. Records are byte-aligned streams of `uint8 tag`, `uint16 body_len`, then `body_len` payload bytes. Scan stops at tag 0x00.

Record types:

- 0xA1 TX_OPEN — `uint64 tx_id`, `uint16 patch_count` (informational)
- 0xA2 BLK_PATCH — `uint32 dst_blk`, then up to 4088 data bytes
- 0xA3 TX_SEAL — `uint64 tx_id`
- 0xA4 BLK_FORGET — `uint64 tx_id`, `uint16 n`, then `n` × `uint32` block indices

Unclean shutdown may leave redundant headers, inode payloads, and allocation maps inconsistent with durable redo records at the tail of the image.

## Recovery contract

Crash copies must be reconciled to a durable view. The rules below are the acceptance criteria for that view — not a build checklist.

### Headers

Only headers with valid magic, a CRC covering the first 68 bytes, and `primary_ok == 1` compete. Prefer the greater `epoch`; break ties with the greater `durable_tx`. A non-primary header never wins, even with a larger epoch.

### Durable redo

A transaction is durable only when a matching TX_SEAL exists. Replay durable work in ascending `tx_id` order. Journal append order is not authoritative. Open transactions without a seal leave no durable effect.

The chosen header's `durable_tx` field may lag the highest sealed id present in the redo area. Sealed work beyond that watermark remains durable and must be applied.

`TX_OPEN`'s `patch_count` field is informational. It must not truncate which sealed `BLK_PATCH` records apply.

### Forget

A sealed `BLK_FORGET` suppresses earlier sealed patches to the named blocks when the forget `tx_id` is greater. An unsealed forget record has no effect.

### Patches and map

Partial patch payloads occupy the start of the destination block; remaining bytes in the 4096-byte block are zero. After replay, rebuild the allocation map at blocks 6–7: mark blocks 0–27 used, plus every live inode `direct[]` block. Report the full 8192-byte map as lowercase hex (16384 characters). Redundant superblocks in rebuilt images match the crash copy.
""",
    )

    w(
        TASK / "environment" / "lib" / "u8_crc.c",
        """#include "kvfs_api.h"

#include <stdint.h>
#include <zlib.h>

uint32_t u8_crc32_bytes(const void *data, size_t len) {
    return (uint32_t)crc32(0, (const unsigned char *)data, (unsigned int)len);
}
""",
    )

    w(
        TASK / "environment" / "lib" / "p7_sb.c",
        """#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "kvfs_internal.h"

kvfs_volume *op_open_vol(const char *path) {
    kvfs_volume *vol = calloc(1, sizeof(*vol));
    if (!vol) return NULL;
    vol->fp = fopen(path, "rb");
    if (!vol->fp) { free(vol); return NULL; }
    fseek(vol->fp, 0, SEEK_END);
    long sz = ftell(vol->fp);
    fseek(vol->fp, 0, SEEK_SET);
    if (sz <= 0) { fclose(vol->fp); free(vol); return NULL; }
    vol->len = (size_t)sz;
    vol->map = malloc(vol->len);
    if (!vol->map) { fclose(vol->fp); free(vol); return NULL; }
    if (fread(vol->map, 1, vol->len, vol->fp) != vol->len) {
        fclose(vol->fp); free(vol->map); free(vol); return NULL;
    }
    return vol;
}

void op_close_vol(kvfs_volume *vol) {
    if (!vol) return;
    if (vol->fp) fclose(vol->fp);
    free(vol->map);
    free(vol);
}

int op_read_block(kvfs_volume *vol, uint32_t blk, void *out, size_t len) {
    if (!vol || !out || len > KVFS_BLOCK_SIZE) return -1;
    size_t off = (size_t)blk * KVFS_BLOCK_SIZE;
    if (off + len > vol->len) return -1;
    memcpy(out, vol->map + off, len);
    return 0;
}

static int header_valid(const uint8_t *blk) {
    const kvfs_super_t *sb = (const kvfs_super_t *)blk;
    if (memcmp(sb->magic, KVFS_MAGIC, 4) != 0) return 0;
    uint32_t got = u8_crc32_bytes(blk, 68);
    return got == sb->sb_crc32 && sb->primary_ok == 1;
}

static int header_prefer_epoch(void) {
    FILE *fp = fopen("/opt/kvfs/config/recovery_policy.ini", "r");
    if (!fp) return 1;
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        char key[64], val[64];
        if (sscanf(line, " %63[^=] = %63s", key, val) != 2) continue;
        if (strcmp(key, "prefer") == 0 && strcmp(val, "durable_tx") == 0) {
            fclose(fp);
            return 0;
        }
    }
    fclose(fp);
    return 1;
}

int resolve_c_pick_header(kvfs_volume *vol, uint32_t *chosen_blk) {
    if (!vol || !chosen_blk) return -1;
    uint8_t b0[KVFS_BLOCK_SIZE], b1[KVFS_BLOCK_SIZE];
    if (op_read_block(vol, 0, b0, KVFS_BLOCK_SIZE)) return -1;
    if (op_read_block(vol, 1, b1, KVFS_BLOCK_SIZE)) return -1;
    int ok0 = header_valid(b0);
    int ok1 = header_valid(b1);
    if (!ok0 && !ok1) return -1;
    if (ok0) {
        *chosen_blk = 0;
        return 0;
    }
    *chosen_blk = 1;
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "lib" / "k9_scan.c",
        """#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <stdint.h>
#include <string.h>

#include "kvfs_internal.h"

int step_a_scan_redo(kvfs_volume *vol, uint64_t *tx_count) {
    if (!vol || !tx_count) return -1;
    uint64_t sealed = 0;
    size_t base = (size_t)KVFS_JOURNAL_BLK * KVFS_BLOCK_SIZE;
    size_t end = base + (size_t)KVFS_JOURNAL_BLKS * KVFS_BLOCK_SIZE;
    size_t pos = base;
    while (pos + 3 < end) {
        uint8_t tag = vol->map[pos];
        if (tag == KVFS_TAG_PAD || tag == 0) break;
        uint16_t body_len;
        memcpy(&body_len, vol->map + pos + 1, 2);
        pos += 3 + body_len;
        if (tag == KVFS_TAG_TX_SEAL) sealed++;
    }
    *tx_count = sealed;
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "lib" / "m3_apply.c",
        (Path(__file__).resolve().parent / "block_volume_env_c" / "m3_apply.c").read_text(),
    )

    w(
        TASK / "environment" / "lib" / "r2_inode.c",
        """#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <string.h>

#include "kvfs_internal.h"

int r2_walk_inodes(kvfs_volume *vol, void (*cb)(const char *name, uint32_t size, void *ctx), void *ctx) {
    if (!vol || !cb) return -1;
    for (uint32_t i = 0; i < KVFS_INODE_CAPACITY; i++) {
        size_t off = (size_t)KVFS_INODE_TABLE_BLK * KVFS_BLOCK_SIZE + (size_t)i * KVFS_INODE_SIZE;
        if (off + KVFS_INODE_SIZE > vol->len) break;
        const kvfs_inode_t *ino = (const kvfs_inode_t *)(vol->map + off);
        if (ino->mode == 0) continue;
        cb(ino->name, ino->size, ctx);
    }
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "tools" / "volpeek.c",
        """#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <stdio.h>
#include <stdlib.h>

static void print_path(const char *name, uint32_t size, void *ctx) {
    (void)size;
    FILE *out = (FILE *)ctx;
    fprintf(out, "%s\\n", name);
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: volpeek <image>\\n");
        return 2;
    }
    kvfs_volume *vol = op_open_vol(argv[1]);
    if (!vol) { perror("open"); return 1; }
    uint32_t chosen = 0;
    if (resolve_c_pick_header(vol, &chosen)) {
        fprintf(stderr, "header pick failed\\n");
        op_close_vol(vol);
        return 1;
    }
    uint64_t sealed = 0;
    step_a_scan_redo(vol, &sealed);
    printf("chosen_superblock=%u sealed_tx=%llu\\n", chosen, (unsigned long long)sealed);
    r2_walk_inodes(vol, print_path, stdout);
    op_close_vol(vol);
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "config" / "recovery_policy.ini",
        """# KVFS batch recovery policy — post-incident defaults
[replay]
order=journal
forget_mode=forward

[bitmap]
metadata_used_end=8

[image]
patch_zero_pad=0
preserve_superblocks=0

[header]
prefer=durable_tx
""",
    )

    w(
        TASK / "environment" / "config" / "build_flags.mk",
        """# Build profile for KVFS tooling
WARNINGS = -Wall -Wextra -Wpedantic
STD = -std=c11
""",
    )

    w(
        TASK / "environment" / "config" / "paths.mk",
        f"""PREFIX = {TASK_ROOT}
BINDIR = $(PREFIX)/bin
LIBDIR = $(PREFIX)/lib
INCDIR = $(PREFIX)/include
""",
    )

    w(
        TASK / "environment" / "data" / "README.txt",
        """Scenario images are read-only crash copies. Baseline digests live in scenario_manifest.json.
""",
    )

    for name, fn in BUILDERS.items():
        img, _ = fn()
        wbin(TASK / "environment" / "data" / "scenarios" / f"{name}.img", bytes(img))

    scenario_sha = {
        name: hashlib.sha256((TASK / "environment" / "data" / "scenarios" / f"{name}.img").read_bytes()).hexdigest()
        for name in SCENARIOS
    }
    w(
        TASK / "environment" / "data" / "scenario_manifest.json",
        json.dumps(scenario_sha, indent=2) + "\n",
    )

    w(TASK / "tests" / "test.sh", """#!/bin/bash

# Verifier dependencies are installed in environment/Dockerfile.

mkdir -p /logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
  --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
""")

    w(TASK / "tests" / "test_outputs.py", emit_tests())

    w(
        TASK / "environment" / "docs" / "scenario_notes.md",
        """# Scenario field notes

Operator observations from post-crash readback. Symptoms only — not a repair plan.

## shard_a

`/notes.txt` still shows the old meeting time after a sealed redo update. `/config/app.cfg` may show an edit that never finished committing.

## shard_b

A retired `/alpha.dat` payload reappears after another file reused the same physical block. Operators expect `/beta.dat` as the live path.

## shard_c

The two volume headers disagree on generation. Ledger vs audit extracts change depending on which header a tool trusts.

## shard_d

`/cache.bin` looks updated, but the free-block map still marks scratch blocks live after a sealed cleanup.

## shard_e

One header advertises a much newer epoch while marked non-primary. Tools that chase the newest epoch return wrong archive bytes.

## shard_f

A higher transaction id was sealed before a lower one in the circular log. The file still shows pre-update content.

## shard_g

`/hold.dat` shows baseline bytes even though a sealed commit landed before a later open transaction logged conflicting patches.

## shard_h

`/layer.dat` still reads baseline after one sealed transaction logged multiple patches to the same data block.

## shard_i

`/lag.dat` still shows early content even though a later sealed transaction exists in the redo area after the headers stopped advancing their durable watermark.

## shard_j

`/keep.dat` loses its sealed payload when an unfinished transaction logged a forget against the same block and then crashed.
""",
    )

    w(TASK / "solution" / "solve.sh", emit_solve_sh())

    fixed_c = Path(__file__).resolve().parent / "block_volume_fixed_c"
    w(TASK / "solution" / "patch" / "m3_apply.c", (fixed_c / "m3_apply.c").read_text())
    w(TASK / "solution" / "patch" / "reconcile.c", (fixed_c / "reconcile.c").read_text())
    w(TASK / "solution" / "patch" / "p7_sb.c", (fixed_c / "p7_sb.c").read_text())

    w(
        TASK / "environment" / "tools" / "reconcile.c",
        (Path(__file__).resolve().parent / "block_volume_env_c" / "reconcile.c").read_text(),
    )

    # extra env files for 20+ count
    extras = {
        "environment/lib/kvfs_internal.h": """#pragma once
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>

typedef struct kvfs_volume {
    FILE *fp;
    uint8_t *map;
    size_t len;
} kvfs_volume;
""",
        "environment/tools/README.txt": "volpeek is read-only; batch recovery via ops/run_recovery.sh after policy review.\n",
        "environment/include/kvfs_crc.h": "#pragma once\n#include <stddef.h>\n#include <stdint.h>\nuint32_t u8_crc32_bytes(const void *data, size_t len);\n",
        "environment/docs/glossary.txt": "KVFS terms mirror vol_format.md.\n",
        "environment/ops/check_image.sh": f"#!/bin/sh\n{TASK_ROOT}/bin/volpeek \"$1\"\n",
        "environment/ops/run_recovery.sh": f"""#!/bin/bash
set -euo pipefail
cd {TASK_ROOT}
./ops/apply_site_policy.sh
make bin/reconcile
mkdir -p /output
bin/reconcile
""",
        "environment/ops/apply_site_policy.sh": f"""#!/bin/bash
set -euo pipefail

POLICY="{TASK_ROOT}/config/recovery_policy.ini"

cat > "$POLICY" <<'EOF'
# KVFS batch recovery policy — post-incident defaults (KVFS-441)
[replay]
order=journal
forget_mode=forward

[bitmap]
metadata_used_end=8

[image]
patch_zero_pad=0
preserve_superblocks=0

[header]
prefer=durable_tx
EOF
""",
        "environment/ops/recovery_status.txt": """Last batch recovery (2026-06-28) completed with exit code 0 but spot checks still show stale payloads, map drift, and missing shards in the report. Ticket KVFS-441 landed mid-validation — review the recovery toolchain before the next run.
""",
        "environment/ops/mount_notes.txt": "Images are flat block arrays, not loop-mounted. Use volpeek for read-only inspection; batch recovery via ops/run_recovery.sh.\n",
        "environment/packaging/version.txt": "kvfs-tools 1.0.0\n",
    }
    for rel, text in extras.items():
        w(TASK / rel, text)

    print(f"Wrote task to {TASK}")


if __name__ == "__main__":
    main()
