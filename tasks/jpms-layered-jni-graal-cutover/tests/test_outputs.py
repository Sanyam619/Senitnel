"""Hard outcome checks for JPMS / JNI / native packaging cutover."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
REPORT = Path("/output/pack-report.json")
REQUIRED_KEPT = ["io.helix.spi.SlotProvider", "io.helix.bridge.NativeHook"]
MATRIX_MODES = ("jvm", "jlink", "native")


@pytest.fixture(scope="session")
def state() -> dict:
    subprocess.run([str(APP / "bin/packctl")], cwd=APP, check=True, timeout=600)
    assert REPORT.is_file(), "packctl did not write /output/pack-report.json"
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert data.get("probe_engine") == "packctl-1"
    modes = data.get("modes")
    assert isinstance(modes, dict)
    lib_dir = APP / "build/lib"
    assert lib_dir.is_dir(), "missing build/lib after packctl"
    assert any(lib_dir.glob("libhelixhook.*")), "JNI shared library was not built"
    assert (APP / "build/mods/helix.app").is_dir(), "JPMS units were not compiled"
    assert (APP / "build/reachability/reflect-config.json").is_file()
    assert (APP / "build/jlink-image/bin/java").is_file()
    return data


def test_k4_v_lane(state: dict) -> None:
    """JVM launch mode reports healthy status."""
    row = state["modes"][MATRIX_MODES[0]]
    assert row["status"] == "ok"


def test_m8_w_lane(state: dict) -> None:
    """jlink launch mode reports healthy status."""
    row = state["modes"][MATRIX_MODES[1]]
    assert row["status"] == "ok"


def test_q2_x_lane(state: dict) -> None:
    """Native launch mode reports healthy status."""
    row = state["modes"][MATRIX_MODES[2]]
    assert row["status"] == "ok"


def test_t6_y_bind(state: dict) -> None:
    """jlink mode keeps SPI service binding enabled."""
    assert state["modes"][MATRIX_MODES[1]]["spi_bound"]
    # Real jlink image must resolve the SPI module, not only a report flag.
    mods = subprocess.check_output(
        [str(APP / "build/jlink-image/bin/java"), "--list-modules"],
        text=True,
    )
    assert "helix.spi" in mods


def test_w1_z_hook(state: dict) -> None:
    """JVM mode resolves the JNI bridge successfully."""
    assert state["modes"][MATRIX_MODES[0]]["jni_bridge"]
    assert state.get("hook") == "io.helix.bridge.NativeHook"


def test_n9_u_keep(state: dict) -> None:
    """Native reflect_kept includes SlotProvider and NativeHook from the contract."""
    kept = set(state["modes"][MATRIX_MODES[2]]["reflect_kept"])
    assert set(REQUIRED_KEPT) <= kept
    disk = json.loads((APP / "build/reachability/reflect-config.json").read_text(encoding="utf-8"))
    names = {row.get("name") for row in disk}
    assert set(REQUIRED_KEPT) <= names
