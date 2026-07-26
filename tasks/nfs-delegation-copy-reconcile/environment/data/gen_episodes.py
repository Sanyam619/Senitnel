#!/usr/bin/env python3
"""Materialise the five recorded NFSv4.2 episodes as binary journal files.

Runs at Docker build time. All journals are little-endian and follow the
formats documented in docs/journal_format.md.
"""

import struct
from pathlib import Path

ROOT = Path("/app/data/episodes")

# Server magic + client magic + copy magic (all 8 bytes, NUL-padded).
SRV_MAGIC  = b"NFSRSVR\x00"
CLI_MAGIC  = b"NFSRCLI\x00"
COPY_MAGIC = b"NFSRCPY\x00"

# Server record tags.
T_RECLAIM_OPEN        = 0x01
T_RECLAIM_DELEG_WRITE = 0x02
T_RECLAIM_DELEG_READ  = 0x03
T_COMMIT_SEAL         = 0x04
T_NAMESPACE_OP        = 0x05
T_COPY_SESSION        = 0x06

# Client record tags.
T_OPEN                = 0x11
T_DELEGATION_HELD     = 0x12
T_RENAME              = 0x13
T_COPY_ISSUE          = 0x14
T_SEQ_TICK            = 0x15

# Namespace ops.
NS_RENAME = 1
NS_UNLINK = 2

# Delegation types.
DT_READ  = 0
DT_WRITE = 1

# Deterministic 16-byte helpers.

def fh(seed: int) -> bytes:
    """Deterministic 16-byte fh with a leading marker byte."""
    return bytes([seed & 0xFF]) + bytes(range(1, 16))


def cid(seed: int) -> bytes:
    return bytes([0xC0 | (seed & 0xF)]) + bytes([seed] * 15)


def owner(seed: int) -> bytes:
    return bytes([0xA0 | (seed & 0xF)]) + bytes([(seed * 3) & 0xFF] * 15)


def ver(seed: int) -> bytes:
    return bytes([(seed * 17 + i) & 0xFF for i in range(8)])


def rec(tag: int, body: bytes) -> bytes:
    if len(body) > 0xFFFF:
        raise ValueError("record body too long")
    return bytes([tag]) + struct.pack("<H", len(body)) + body


# ----- Body encoders -----

def reclaim_open(client_id, opener, seq, handle):
    return client_id + opener + struct.pack("<Q", seq) + handle  # 56


def reclaim_deleg(client_id, seq, handle, epoch):
    return client_id + struct.pack("<Q", seq) + handle + struct.pack("<Q", epoch)  # 48


def commit_seal(seq, verifier, durable):
    return struct.pack("<Q", seq) + verifier + struct.pack("<Q", durable)  # 24


def namespace_op(op, src, dst, ts_ms):
    return bytes([op]) + src + dst + struct.pack("<Q", ts_ms)  # 41


def copy_session(src, dst, session_id, state):
    return src + dst + struct.pack("<Q", session_id) + bytes([state])  # 41


def open_rec(seq, handle, mode, ts):
    return struct.pack("<Q", seq) + handle + struct.pack("<I", mode) + struct.pack("<Q", ts)  # 36


def delegation_held(seq, handle, dtype, epoch):
    return struct.pack("<Q", seq) + handle + bytes([dtype]) + struct.pack("<Q", epoch)  # 33


def rename_rec(src, dst, seq, ts, backed):
    return src + dst + struct.pack("<Q", seq) + struct.pack("<Q", ts) + bytes([backed])  # 49


def copy_issue(src, dst, session_id, offset, length):
    return src + dst + struct.pack("<Q", session_id) + struct.pack("<Q", offset) + struct.pack("<Q", length)  # 48


def seq_tick(new_seq):
    return struct.pack("<Q", new_seq)  # 8


# ----- Log builders -----

def server_header(boot_prev, boot_curr, grace_ms, deadline_ms):
    return (
        SRV_MAGIC
        + struct.pack("<I", 1)    # version
        + struct.pack("<I", 0)    # pad
        + struct.pack("<Q", boot_prev)
        + struct.pack("<Q", boot_curr)
        + struct.pack("<I", grace_ms)
        + struct.pack("<I", deadline_ms)
    )


def client_header(client_id, owner_seq_start):
    return (
        CLI_MAGIC
        + struct.pack("<I", 1)   # version
        + struct.pack("<I", 0)   # pad
        + client_id
        + struct.pack("<Q", owner_seq_start)
    )


def copy_intent(source, dest, session_id, total, flushed, verifier, committed, issue_ts):
    return (
        COPY_MAGIC
        + struct.pack("<I", 1)
        + struct.pack("<I", 0)
        + source
        + dest
        + struct.pack("<Q", session_id)
        + struct.pack("<Q", total)
        + struct.pack("<Q", flushed)
        + verifier
        + bytes([committed])
        + b"\x00" * 7
        + struct.pack("<Q", issue_ts)
    )


def write_files(ep, server_log, cliA_log, cliB_log, ci, ns_lines):
    dst = ROOT / ep
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "server_reclaim.log").write_bytes(server_log)
    (dst / "client_a_ops.log").write_bytes(cliA_log)
    (dst / "client_b_ops.log").write_bytes(cliB_log)
    (dst / "copy_intent.rec").write_bytes(ci)
    (dst / "namespace.snap").write_text(ns_lines, encoding="utf-8")


def hexfh(f):
    return f.hex()


# ===== Episode ALPHA — grace-window edge, rename stranded =====
# Client A held a write delegation and issued a delegation-backed RENAME
# just before the reboot. The reclaim never lands in the current boot
# epoch (grace window closes), so the delegation is released AND the
# unacknowledged delegation-backed rename cannot take effect.

def build_alpha():
    src_fh = fh(0xA0)
    ren_fh = fh(0xAA)
    dst_fh = fh(0xA1)
    cliA = cid(1)
    cliB = cid(2)
    v = ver(1)

    # Server: no RECLAIM_DELEG under new epoch for src_fh, only an old-epoch RECLAIM_DELEG.
    # No NAMESPACE_OP either — server didn't ack the rename before reboot.
    srv = server_header(boot_prev=1000, boot_curr=1001, grace_ms=500, deadline_ms=450)
    srv += rec(T_RECLAIM_DELEG_WRITE, reclaim_deleg(cliA, seq=100, handle=src_fh, epoch=1000))
    srv += rec(T_COPY_SESSION, copy_session(src_fh, dst_fh, session_id=7000, state=1))
    srv += bytes([0])

    a = client_header(cliA, owner_seq_start=100)
    a += rec(T_OPEN, open_rec(seq=101, handle=src_fh, mode=3, ts=1000))
    a += rec(T_DELEGATION_HELD, delegation_held(seq=101, handle=src_fh, dtype=DT_WRITE, epoch=1000))
    a += rec(T_RENAME, rename_rec(src_fh, ren_fh, seq=110, ts=1050, backed=1))
    a += rec(T_SEQ_TICK, seq_tick(111))
    a += bytes([0])

    b = client_header(cliB, owner_seq_start=200)
    b += rec(T_OPEN, open_rec(seq=201, handle=src_fh, mode=1, ts=1100))
    b += rec(T_DELEGATION_HELD, delegation_held(seq=201, handle=src_fh, dtype=DT_READ, epoch=1000))
    b += rec(T_COPY_ISSUE, copy_issue(src_fh, dst_fh, session_id=7000, offset=0, length=4096))
    b += rec(T_SEQ_TICK, seq_tick(202))
    b += bytes([0])

    ci = copy_intent(src_fh, dst_fh, session_id=7000,
                     total=8192, flushed=4096, verifier=v, committed=0,
                     issue_ts=1200)
    ns = (f"{hexfh(src_fh)} /vol/alpha/subject.dat\n"
          f"{hexfh(dst_fh)} /vol/alpha/subject.copy\n")
    write_files("alpha", srv, a, b, ci, ns)


# ===== Episode BETA — two clients reclaim write delegations on same fh =====
# Both reclaims valid under current epoch. Conflict resolver: smaller
# client_id keeps write, other downgraded to share. Client B (larger id)
# ends up on share -> copy restarted.

def build_beta():
    src_fh = fh(0xB0)
    dst_fh = fh(0xB1)
    cliA = cid(3)   # smaller id (0xC3...)
    cliB = cid(5)   # larger id  (0xC5...)
    v = ver(2)

    srv = server_header(boot_prev=2000, boot_curr=2001, grace_ms=1000, deadline_ms=800)
    srv += rec(T_RECLAIM_DELEG_WRITE, reclaim_deleg(cliA, seq=150, handle=src_fh, epoch=2001))
    srv += rec(T_RECLAIM_DELEG_WRITE, reclaim_deleg(cliB, seq=155, handle=src_fh, epoch=2001))
    srv += rec(T_COPY_SESSION, copy_session(src_fh, dst_fh, session_id=8000, state=1))
    srv += bytes([0])

    a = client_header(cliA, owner_seq_start=150)
    a += rec(T_OPEN, open_rec(seq=151, handle=src_fh, mode=3, ts=2000))
    a += rec(T_DELEGATION_HELD, delegation_held(seq=150, handle=src_fh, dtype=DT_WRITE, epoch=2001))
    a += bytes([0])

    b = client_header(cliB, owner_seq_start=155)
    b += rec(T_OPEN, open_rec(seq=156, handle=src_fh, mode=3, ts=2100))
    b += rec(T_DELEGATION_HELD, delegation_held(seq=155, handle=src_fh, dtype=DT_WRITE, epoch=2001))
    b += rec(T_COPY_ISSUE, copy_issue(src_fh, dst_fh, session_id=8000, offset=0, length=2048))
    b += bytes([0])

    ci = copy_intent(src_fh, dst_fh, session_id=8000,
                     total=8192, flushed=2048, verifier=v, committed=0,
                     issue_ts=2200)
    ns = f"{hexfh(src_fh)} /vol/beta/shared.dat\n{hexfh(dst_fh)} /vol/beta/shared.copy\n"
    write_files("beta", srv, a, b, ci, ns)


# ===== Episode GAMMA — rename race, delegation-backed rename wins =====
# Client A holds a write delegation on src_fh, issues a delegation-backed
# RENAME src->dst-hidden after copy issue. Copy is invalidated because
# src_fh no longer maps to the object client B was reading.

def build_gamma():
    src_fh = fh(0xC0)
    new_fh = fh(0xC1)
    dest_fh = fh(0xC2)
    cliA = cid(6)
    cliB = cid(7)
    v = ver(3)

    srv = server_header(boot_prev=3000, boot_curr=3001, grace_ms=1000, deadline_ms=900)
    srv += rec(T_RECLAIM_DELEG_WRITE, reclaim_deleg(cliA, seq=210, handle=src_fh, epoch=3001))
    srv += rec(T_COPY_SESSION, copy_session(src_fh, dest_fh, session_id=9000, state=1))
    srv += rec(T_NAMESPACE_OP, namespace_op(NS_RENAME, src_fh, new_fh, ts_ms=505))
    srv += bytes([0])

    a = client_header(cliA, owner_seq_start=210)
    a += rec(T_OPEN, open_rec(seq=211, handle=src_fh, mode=3, ts=3000))
    a += rec(T_DELEGATION_HELD, delegation_held(seq=210, handle=src_fh, dtype=DT_WRITE, epoch=3001))
    a += rec(T_RENAME, rename_rec(src_fh, new_fh, seq=215, ts=505, backed=1))
    a += rec(T_SEQ_TICK, seq_tick(216))
    a += bytes([0])

    b = client_header(cliB, owner_seq_start=180)
    b += rec(T_OPEN, open_rec(seq=181, handle=src_fh, mode=1, ts=3100))
    b += rec(T_DELEGATION_HELD, delegation_held(seq=180, handle=src_fh, dtype=DT_READ, epoch=3001))
    b += rec(T_COPY_ISSUE, copy_issue(src_fh, dest_fh, session_id=9000, offset=0, length=1024))
    b += bytes([0])

    # Copy was issued at ts=400 (BEFORE the rename at ts=505).
    ci = copy_intent(src_fh, dest_fh, session_id=9000,
                     total=4096, flushed=1024, verifier=v, committed=0,
                     issue_ts=400)
    ns = (f"{hexfh(new_fh)} /vol/gamma/renamed.dat\n"
          f"{hexfh(dest_fh)} /vol/gamma/copy.dat\n")
    write_files("gamma", srv, a, b, ci, ns)


# ===== Episode DELTA — unbacked rename accepted pre-reboot =====
# RENAME with delegation_backed=0 that server had already accepted
# (visible in server NAMESPACE_OP). Client B's copy still targets the
# stale src_fh, so it invalidates. Delegation state stays held for A
# (its reclaim is valid).

def build_delta():
    src_fh = fh(0xD0)
    new_fh = fh(0xD1)
    dest_fh = fh(0xD2)
    cliA = cid(8)
    cliB = cid(9)
    v = ver(4)

    srv = server_header(boot_prev=4000, boot_curr=4001, grace_ms=800, deadline_ms=700)
    srv += rec(T_RECLAIM_DELEG_WRITE, reclaim_deleg(cliA, seq=310, handle=src_fh, epoch=4001))
    srv += rec(T_NAMESPACE_OP, namespace_op(NS_RENAME, src_fh, new_fh, ts_ms=250))
    srv += rec(T_COPY_SESSION, copy_session(src_fh, dest_fh, session_id=10000, state=1))
    srv += bytes([0])

    a = client_header(cliA, owner_seq_start=310)
    a += rec(T_OPEN, open_rec(seq=311, handle=src_fh, mode=3, ts=4000))
    a += rec(T_DELEGATION_HELD, delegation_held(seq=310, handle=src_fh, dtype=DT_WRITE, epoch=4001))
    a += rec(T_RENAME, rename_rec(src_fh, new_fh, seq=312, ts=250, backed=0))
    a += bytes([0])

    b = client_header(cliB, owner_seq_start=280)
    b += rec(T_OPEN, open_rec(seq=281, handle=src_fh, mode=1, ts=4050))
    b += rec(T_COPY_ISSUE, copy_issue(src_fh, dest_fh, session_id=10000, offset=0, length=512))
    b += rec(T_SEQ_TICK, seq_tick(282))
    b += bytes([0])

    # Copy issued at ts=300 (AFTER server accepted rename at 250 — but
    # client B didn't know; the copy still names the stale src_fh).
    ci = copy_intent(src_fh, dest_fh, session_id=10000,
                     total=4096, flushed=512, verifier=v, committed=0,
                     issue_ts=300)
    ns = (f"{hexfh(new_fh)} /vol/delta/renamed.dat\n"
          f"{hexfh(dest_fh)} /vol/delta/copy.dat\n")
    write_files("delta", srv, a, b, ci, ns)


# ===== Episode EPSILON — copy fully completed pre-reboot =====
# COMMIT_SEAL with matching verifier, bytes_flushed == total_bytes,
# committed_flag=1. Copy resolution must be `completed` (idempotent).

def build_epsilon():
    src_fh = fh(0xE0)
    dest_fh = fh(0xE1)
    cliA = cid(10)
    cliB = cid(11)
    v = ver(5)

    srv = server_header(boot_prev=5000, boot_curr=5001, grace_ms=1000, deadline_ms=900)
    srv += rec(T_RECLAIM_DELEG_WRITE, reclaim_deleg(cliA, seq=410, handle=src_fh, epoch=5001))
    srv += rec(T_COPY_SESSION, copy_session(src_fh, dest_fh, session_id=11000, state=2))
    srv += rec(T_COMMIT_SEAL, commit_seal(seq=411, verifier=v, durable=16384))
    srv += bytes([0])

    a = client_header(cliA, owner_seq_start=410)
    a += rec(T_OPEN, open_rec(seq=411, handle=src_fh, mode=3, ts=5000))
    a += rec(T_DELEGATION_HELD, delegation_held(seq=410, handle=src_fh, dtype=DT_WRITE, epoch=5001))
    a += bytes([0])

    b = client_header(cliB, owner_seq_start=420)
    b += rec(T_OPEN, open_rec(seq=421, handle=src_fh, mode=1, ts=5100))
    b += rec(T_DELEGATION_HELD, delegation_held(seq=420, handle=src_fh, dtype=DT_READ, epoch=5001))
    b += rec(T_COPY_ISSUE, copy_issue(src_fh, dest_fh, session_id=11000, offset=0, length=16384))
    b += rec(T_SEQ_TICK, seq_tick(422))
    b += bytes([0])

    ci = copy_intent(src_fh, dest_fh, session_id=11000,
                     total=16384, flushed=16384, verifier=v, committed=1,
                     issue_ts=5200)
    ns = (f"{hexfh(src_fh)} /vol/epsilon/subject.dat\n"
          f"{hexfh(dest_fh)} /vol/epsilon/subject.copy\n")
    write_files("epsilon", srv, a, b, ci, ns)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    build_alpha()
    build_beta()
    build_gamma()
    build_delta()
    build_epsilon()
    # Emit an episode manifest with the focused_fh for each name; the
    # test harness re-derives the same values from copy_intent.rec.
    focused = {
        "alpha":   fh(0xA0).hex(),
        "beta":    fh(0xB0).hex(),
        "gamma":   fh(0xC0).hex(),
        "delta":   fh(0xD0).hex(),
        "epsilon": fh(0xE0).hex(),
    }
    import json
    (ROOT.parent / "episode_manifest.json").write_text(
        json.dumps({"episodes": focused}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
