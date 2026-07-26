#!/usr/bin/env python3
"""Materialize binary shelf fixtures for the btrfs lab image build."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "btrfs"


def w(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def main() -> None:
    payloads = {
        "o_alpha": b"ORIGIN-ALPHA-v1\n",
        "o_beta": b"ORIGIN-BETA-v1\n",
        "o_gamma": b"ORIGIN-GAMMA-v1\n",
        "o_delta": b"ORIGIN-DELTA-v1\n",
        "o_omega": b"ORIGIN-OMEGA-v1\n",
        "su-alpha": b"SNAP-ALPHA-SEALED\n",
        "su-beta": b"SNAP-BETA-SEALED\n",
        "su-gamma": b"SNAP-GAMMA-SEALED\n",
        "su-delta": b"SNAP-DELTA-SEALED\n",
        "su-omega": b"SNAP-OMEGA-SEALED\n",
        "su-bogus": b"SNAP-BOGUS-BEYOND\n",
        "d_alpha": b"DECOY-ALPHA\n",
        "d_beta": b"DECOY-BETA\n",
        "d_gamma": b"DECOY-GAMMA\n",
        "d_delta": b"DECOY-DELTA\n",
        "d_omega": b"DECOY-OMEGA\n",
    }
    for name, body in payloads.items():
        if name.startswith("o_"):
            w(ROOT / "origins" / f"{name}.bin", body)
        elif name.startswith("su-"):
            w(ROOT / "snaps" / "payloads" / f"{name}.bin", body)
        elif name.startswith("d_"):
            w(ROOT / "decoys" / f"{name}.bin", body)

    lane_snap = {
        "alpha": "su-alpha",
        "beta": "su-beta",
        "gamma": "su-gamma",
        "delta": "su-delta",
        "omega": "su-omega",
    }
    for lane, snap in lane_snap.items():
        sealed = payloads[snap]
        decoy = payloads[f"d_{lane}"]
        w(ROOT / "volumes" / lane / "sealed" / "payload.bin", sealed)
        w(ROOT / "volumes" / lane / "decoy" / "payload.bin", decoy)
        w(ROOT / "volumes" / lane / "host" / "marker.flag", b"host\n")

    w(ROOT / "meta" / "runtime.tsv", b"")
    print("fixtures ok")


if __name__ == "__main__":
    main()
