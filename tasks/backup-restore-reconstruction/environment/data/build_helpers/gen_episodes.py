#!/usr/bin/env python3
"""Materialise episode crash-export fixtures under data/episodes/.

Run at image build time; removed from the image after generation.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "episodes"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))


def write_bin(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def gen_alpha() -> dict:
    ep = ROOT / "alpha"
    if ep.exists():
        shutil.rmtree(ep)
    # Seal at epoch 10; post-seal reclaim of beacon is provisional.
    write_jsonl(
        ep / "coordinator.jsonl",
        [
            {"tag": "admit", "epoch": 4, "ts": 400, "lab": "mesa"},
            {"tag": "admit", "epoch": 5, "ts": 500, "lab": "cinder"},
            {"tag": "seal", "epoch": 10, "ts": 1000, "volume_id": "vol-alpha"},
            {"tag": "reclaim", "epoch": 12, "ts": 1200, "lab": "beacon"},
            {"tag": "admit", "epoch": 13, "ts": 1300, "lab": "atlas"},
        ],
    )
    write_jsonl(
        ep / "participant_a.jsonl",
        [
            {"tag": "note", "ts": 450, "lab": "mesa", "msg": "sync-ok"},
            {"tag": "note", "ts": 550, "lab": "cinder", "msg": "sync-ok"},
        ],
    )
    write_jsonl(
        ep / "participant_b.jsonl",
        [{"tag": "note", "ts": 1250, "lab": "beacon", "msg": "late-reclaim"}],
    )
    sealed = b"ALPHA-SEALED-POOL-v1\n"
    decoy = b"ALPHA-DECOY-POOL-wrong\n"
    write_bin(ep / "shelves" / "sealed" / "payload.bin", sealed)
    write_bin(ep / "shelves" / "decoy" / "payload.bin", decoy)
    write_bin(ep / "shelves" / "staging" / "payload.bin", decoy)
    write_json(
        ep / "volume_seal.json",
        {
            "volume_id": "vol-alpha",
            "seal_epoch": 10,
            "lineage": "sealed",
            "shelf_key": "sealed",
        },
    )
    write_json(
        ep / "leases.json",
        {
            "slot": "borrow_primary",
            "claims": [
                {
                    "peer": "ridge",
                    "live": True,
                    "sealed": True,
                    "ts": 800,
                    "token": "a-lease-1",
                }
            ],
        },
    )
    write_json(ep / "quarantine.json", {"peers": {"ridge": False, "beacon": False}})
    # Single fragment; order trivial.
    parts = [{"id": "p0", "offset": 0, "seal_ord": 1, "bytes_hex": b"A1".hex()}]
    write_json(ep / "fragments.json", {"parts": parts})
    frag = bytes.fromhex(parts[0]["bytes_hex"])
    write_json(
        ep / "recipe.json",
        {"episode": "alpha", "focus": "late-reclaim", "expected_shelf": "sealed"},
    )
    return {
        "roster_final": ["cinder", "mesa"],
        "borrow_peer": "ridge",
        "payload_sha256": sha256_bytes(sealed),
        "fragment_sha256": sha256_bytes(frag),
        "decision": "provisional_dropped",
    }


def gen_beta() -> dict:
    ep = ROOT / "beta"
    if ep.exists():
        shutil.rmtree(ep)
    write_jsonl(
        ep / "coordinator.jsonl",
        [
            {"tag": "admit", "epoch": 2, "ts": 200, "lab": "mesa"},
            {"tag": "seal", "epoch": 8, "ts": 800, "volume_id": "vol-beta"},
        ],
    )
    write_jsonl(ep / "participant_a.jsonl", [{"tag": "note", "ts": 210, "lab": "mesa", "msg": "ok"}])
    write_jsonl(ep / "participant_b.jsonl", [{"tag": "note", "ts": 220, "lab": "mesa", "msg": "ok"}])
    sealed = b"BETA-SEALED-POOL-v1\n"
    decoy = b"BETA-DECOY-POOL-wrong\n"
    write_bin(ep / "shelves" / "sealed" / "payload.bin", sealed)
    write_bin(ep / "shelves" / "decoy" / "payload.bin", decoy)
    write_json(
        ep / "volume_seal.json",
        {
            "volume_id": "vol-beta",
            "seal_epoch": 8,
            "lineage": "sealed",
            "shelf_key": "sealed",
        },
    )
    # Dual polarities in one episode:
    # - earlier unsealed (atlas@50) loses to sealed precedence
    # - later sealed (mesa@200) loses to earliest-ts among sealed (ridge@100)
    write_json(
        ep / "leases.json",
        {
            "slot": "borrow_primary",
            "claims": [
                {
                    "peer": "ridge",
                    "live": True,
                    "sealed": True,
                    "ts": 100,
                    "token": "b-sealed",
                },
                {
                    "peer": "atlas",
                    "live": True,
                    "sealed": False,
                    "ts": 50,
                    "token": "b-earlier-unsealed",
                },
                {
                    "peer": "mesa",
                    "live": True,
                    "sealed": True,
                    "ts": 200,
                    "token": "b-later-sealed",
                },
            ],
        },
    )
    write_json(
        ep / "quarantine.json",
        {"peers": {"ridge": False, "atlas": False, "mesa": False}},
    )
    parts = [{"id": "p0", "offset": 0, "seal_ord": 1, "bytes_hex": b"B1".hex()}]
    write_json(ep / "fragments.json", {"parts": parts})
    write_json(ep / "recipe.json", {"episode": "beta", "focus": "dual-lease"})
    return {
        "roster_final": ["mesa"],
        "borrow_peer": "ridge",
        "payload_sha256": sha256_bytes(sealed),
        "fragment_sha256": sha256_bytes(bytes.fromhex(parts[0]["bytes_hex"])),
        "decision": "sealed_lease_wins",
    }


def gen_gamma() -> dict:
    ep = ROOT / "gamma"
    if ep.exists():
        shutil.rmtree(ep)
    write_jsonl(
        ep / "coordinator.jsonl",
        [
            {"tag": "admit", "epoch": 1, "ts": 100, "lab": "cinder"},
            {"tag": "seal", "epoch": 5, "ts": 500, "volume_id": "vol-gamma"},
        ],
    )
    write_jsonl(ep / "participant_a.jsonl", [{"tag": "note", "ts": 110, "lab": "cinder", "msg": "ok"}])
    write_jsonl(ep / "participant_b.jsonl", [{"tag": "note", "ts": 120, "lab": "cinder", "msg": "ok"}])
    sealed = b"GAMMA-SEALED-AUTHORITATIVE\n"
    decoy = b"GAMMA-DECOY-LOOKS-NEWER\n"
    staging = b"GAMMA-STAGING-PARTIAL\n"
    write_bin(ep / "shelves" / "sealed" / "payload.bin", sealed)
    write_bin(ep / "shelves" / "decoy" / "payload.bin", decoy)
    write_bin(ep / "shelves" / "staging" / "payload.bin", staging)
    write_json(
        ep / "volume_seal.json",
        {
            "volume_id": "vol-gamma",
            "seal_epoch": 5,
            "lineage": "sealed",
            "shelf_key": "sealed",
        },
    )
    write_json(
        ep / "leases.json",
        {
            "slot": "borrow_primary",
            "claims": [
                {
                    "peer": "mesa",
                    "live": True,
                    "sealed": True,
                    "ts": 400,
                    "token": "g-lease",
                }
            ],
        },
    )
    write_json(ep / "quarantine.json", {"peers": {"mesa": False}})
    parts = [{"id": "p0", "offset": 0, "seal_ord": 1, "bytes_hex": b"G1".hex()}]
    write_json(ep / "fragments.json", {"parts": parts})
    write_json(ep / "recipe.json", {"episode": "gamma", "focus": "decoy-shelf"})
    return {
        "roster_final": ["cinder"],
        "borrow_peer": "mesa",
        "payload_sha256": sha256_bytes(sealed),
        "fragment_sha256": sha256_bytes(bytes.fromhex(parts[0]["bytes_hex"])),
        "decision": "sealed_lineage",
    }


def gen_delta() -> dict:
    ep = ROOT / "delta"
    if ep.exists():
        shutil.rmtree(ep)
    write_jsonl(
        ep / "coordinator.jsonl",
        [
            {"tag": "admit", "epoch": 3, "ts": 300, "lab": "ridge"},
            {"tag": "seal", "epoch": 7, "ts": 700, "volume_id": "vol-delta"},
        ],
    )
    write_jsonl(ep / "participant_a.jsonl", [{"tag": "note", "ts": 310, "lab": "ridge", "msg": "ok"}])
    write_jsonl(ep / "participant_b.jsonl", [{"tag": "note", "ts": 320, "lab": "ridge", "msg": "ok"}])
    sealed = b"DELTA-SEALED-POOL-v1\n"
    decoy = b"DELTA-DECOY-POOL\n"
    write_bin(ep / "shelves" / "sealed" / "payload.bin", sealed)
    write_bin(ep / "shelves" / "decoy" / "payload.bin", decoy)
    write_json(
        ep / "volume_seal.json",
        {
            "volume_id": "vol-delta",
            "seal_epoch": 7,
            "lineage": "sealed",
            "shelf_key": "sealed",
        },
    )
    write_json(
        ep / "leases.json",
        {
            "slot": "borrow_primary",
            "claims": [
                {
                    "peer": "mesa",
                    "live": True,
                    "sealed": True,
                    "ts": 600,
                    "token": "d-lease",
                }
            ],
        },
    )
    write_json(ep / "quarantine.json", {"peers": {"mesa": False}})
    # seal_ord reverses offset order: correct weave is AAA then BBB.
    a = b"AAA-DELTA-HEAD"
    b = b"BBB-DELTA-TAIL"
    parts = [
        {"id": "p0", "offset": 0, "seal_ord": 2, "bytes_hex": b.hex()},
        {"id": "p1", "offset": 100, "seal_ord": 1, "bytes_hex": a.hex()},
    ]
    write_json(ep / "fragments.json", {"parts": parts})
    write_json(ep / "recipe.json", {"episode": "delta", "focus": "fragment-order"})
    correct = a + b
    return {
        "roster_final": ["ridge"],
        "borrow_peer": "mesa",
        "payload_sha256": sha256_bytes(sealed),
        "fragment_sha256": sha256_bytes(correct),
        "decision": "seal_ordinal_weave",
    }


def gen_epsilon() -> dict:
    ep = ROOT / "epsilon"
    if ep.exists():
        shutil.rmtree(ep)
    write_jsonl(
        ep / "coordinator.jsonl",
        [
            {"tag": "admit", "epoch": 2, "ts": 200, "lab": "beacon"},
            {"tag": "admit", "epoch": 3, "ts": 300, "lab": "mesa"},
            {"tag": "seal", "epoch": 9, "ts": 900, "volume_id": "vol-epsilon"},
        ],
    )
    write_jsonl(
        ep / "participant_a.jsonl",
        [
            {"tag": "note", "ts": 210, "lab": "beacon", "msg": "ok"},
            {"tag": "note", "ts": 310, "lab": "mesa", "msg": "ok"},
        ],
    )
    write_jsonl(ep / "participant_b.jsonl", [{"tag": "note", "ts": 250, "lab": "beacon", "msg": "ok"}])
    sealed = b"EPSILON-SEALED-POOL-v1\n"
    decoy = b"EPSILON-DECOY-POOL\n"
    write_bin(ep / "shelves" / "sealed" / "payload.bin", sealed)
    write_bin(ep / "shelves" / "decoy" / "payload.bin", decoy)
    write_json(
        ep / "volume_seal.json",
        {
            "volume_id": "vol-epsilon",
            "seal_epoch": 9,
            "lineage": "sealed",
            "shelf_key": "sealed",
        },
    )
    # ridge sealed but quarantined; atlas live unsealed clear; cinder sealed live clear.
    write_json(
        ep / "leases.json",
        {
            "slot": "borrow_primary",
            "claims": [
                {
                    "peer": "ridge",
                    "live": True,
                    "sealed": True,
                    "ts": 500,
                    "token": "e-ridge",
                },
                {
                    "peer": "atlas",
                    "live": True,
                    "sealed": False,
                    "ts": 850,
                    "token": "e-atlas",
                },
                {
                    "peer": "cinder",
                    "live": True,
                    "sealed": True,
                    "ts": 400,
                    "token": "e-cinder",
                },
            ],
        },
    )
    write_json(
        ep / "quarantine.json",
        {"peers": {"ridge": True, "atlas": False, "cinder": False}},
    )
    parts = [{"id": "p0", "offset": 0, "seal_ord": 1, "bytes_hex": b"E1".hex()}]
    write_json(ep / "fragments.json", {"parts": parts})
    write_json(ep / "recipe.json", {"episode": "epsilon", "focus": "policy-quarantine"})
    return {
        "roster_final": ["beacon", "mesa"],
        "borrow_peer": "cinder",
        "payload_sha256": sha256_bytes(sealed),
        "fragment_sha256": sha256_bytes(bytes.fromhex(parts[0]["bytes_hex"])),
        "decision": "clear_sealed_borrow",
    }


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    expected = {
        "alpha": gen_alpha(),
        "beta": gen_beta(),
        "gamma": gen_gamma(),
        "delta": gen_delta(),
        "epsilon": gen_epsilon(),
    }
    # Emit reference JSON on stdout for local authoring checks.
    print(json.dumps(expected, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
