import json
import shutil
import subprocess

import pytest
from pathlib import Path

OPT = Path("/opt/bgplab")
OUT = Path("/output")
CONVERGE = OPT / "bin" / "converge"

FIB_GT = json.loads("""{
  "alpha": [
    {
      "prefix": "10.1.0.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65010
      ]
    },
    {
      "prefix": "10.1.1.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65020,
        65010
      ]
    },
    {
      "prefix": "10.1.2.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65011
      ]
    },
    {
      "prefix": "10.1.3.0/24",
      "peer": "peer_b",
      "next_hop": "192.0.2.20",
      "as_path": [
        65200,
        65012
      ]
    }
  ],
  "bravo": [
    {
      "prefix": "10.2.0.0/24",
      "peer": "peer_c",
      "next_hop": "192.0.2.30",
      "as_path": [
        65300,
        65030
      ]
    },
    {
      "prefix": "10.2.1.0/24",
      "peer": "peer_b",
      "next_hop": "192.0.2.20",
      "as_path": [
        65200,
        65031
      ]
    }
  ],
  "charlie": [
    {
      "prefix": "10.3.0.0/24",
      "peer": "peer_b",
      "next_hop": "192.0.2.20",
      "as_path": [
        65200,
        65040
      ]
    },
    {
      "prefix": "10.3.1.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65041
      ]
    },
    {
      "prefix": "10.3.2.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65042
      ]
    }
  ],
  "delta": [
    {
      "prefix": "10.4.0.0/24",
      "peer": "peer_c",
      "next_hop": "192.0.2.30",
      "as_path": [
        65300,
        65050
      ]
    },
    {
      "prefix": "10.4.1.0/24",
      "peer": "peer_d",
      "next_hop": "192.0.2.40",
      "as_path": [
        65400,
        65051
      ]
    }
  ],
  "india": [
    {
      "prefix": "10.5.0.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65150
      ]
    },
    {
      "prefix": "10.5.1.0/24",
      "peer": "peer_c",
      "next_hop": "192.0.2.30",
      "as_path": [
        65300,
        65150
      ]
    }
  ],
  "juliet": [
    {
      "prefix": "10.6.0.0/24",
      "peer": "peer_b",
      "next_hop": "192.0.2.20",
      "as_path": [
        65200,
        65210
      ]
    },
    {
      "prefix": "10.6.1.0/24",
      "peer": "peer_a",
      "next_hop": "192.0.2.10",
      "as_path": [
        65100,
        65211
      ]
    }
  ]
}""")
LEAKS_GT = json.loads("""{
  "items": [
    {
      "prefix": "10.1.3.0/24",
      "peer": "peer_a",
      "as_path": [
        65100,
        65012
      ]
    },
    {
      "prefix": "10.2.0.0/24",
      "peer": "peer_c",
      "as_path": [
        65300,
        65100
      ]
    },
    {
      "prefix": "10.2.1.0/24",
      "peer": "peer_b",
      "as_path": [
        65200,
        65200
      ]
    },
    {
      "prefix": "10.3.1.0/24",
      "peer": "peer_b",
      "as_path": [
        65200,
        65041
      ]
    },
    {
      "prefix": "10.3.2.0/24",
      "peer": "peer_b",
      "as_path": [
        65200,
        65042
      ]
    },
    {
      "prefix": "10.4.1.0/24",
      "peer": "peer_d",
      "as_path": [
        65400,
        65400
      ]
    },
    {
      "prefix": "10.5.0.0/24",
      "peer": "peer_b",
      "as_path": [
        65200,
        65199
      ]
    },
    {
      "prefix": "10.6.0.0/24",
      "peer": "peer_a",
      "as_path": [
        65100,
        65210
      ]
    }
  ]
}""")


def run_tool():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    subprocess.run(
        ["go", "build", "-o", "bin/converge", "./cmd/converge"],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    subprocess.run(
        [
            str(CONVERGE),
            "--policy",
            "/opt/bgplab/data/policy.toml",
            "--scenarios",
            "/opt/bgplab/data/scenarios",
            "--out",
            "/output",
        ],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    fib = json.loads((OUT / "fib.json").read_text())
    leaks = json.loads((OUT / "leaks.json").read_text())
    return fib, leaks


@pytest.fixture(scope="module")
def tool_output():
    return run_tool()


def test_golf(tool_output):
    """Declared output artifacts exist at the instructed paths."""
    assert (OUT / "fib.json").is_file()
    assert (OUT / "leaks.json").is_file()


def test_hotel(tool_output):
    """Back-to-back runs emit identical fib and leak payloads."""
    first_fib, first_leaks = tool_output
    second_fib, second_leaks = run_tool()
    assert second_fib == first_fib
    assert second_leaks == first_leaks


def test_alpha(tool_output):
    """Alpha edge lab: attested origins win and export holds block only their scoped prefix."""
    fib, _ = tool_output
    assert fib["alpha"] == FIB_GT["alpha"]


def test_bravo(tool_output):
    """Bravo metro desk: loop-shaped exports lose and MED-aware selection respects neighbors."""
    fib, _ = tool_output
    assert fib["bravo"] == FIB_GT["bravo"]


def test_charlie(tool_output):
    """Charlie research WAN: stale-attestation holds apply per prefix without starving siblings."""
    fib, _ = tool_output
    assert fib["charlie"] == FIB_GT["charlie"]


def test_delta(tool_output):
    """Delta peering refresh: newest attestation serial governs after a revoked row is superseded."""
    fib, _ = tool_output
    assert fib["delta"] == FIB_GT["delta"]


def test_india(tool_output):
    """India IX rollup: aggregate attestations cover specifics and path-length limits bind correctly."""
    fib, _ = tool_output
    assert fib["india"] == FIB_GT["india"]


def test_juliet(tool_output):
    """Juliet transit re-home: non-export holds block peers and serial rivalry picks the valid row."""
    fib, _ = tool_output
    assert fib["juliet"] == FIB_GT["juliet"]


def test_echo(tool_output):
    """Leak ledger is populated, sorted, and uses the instructed item shape."""
    _, leaks = tool_output
    items = leaks.get("items")
    assert isinstance(items, list)
    assert items, "expected a non-empty leak catalog after trust repair"
    assert items == sorted(items, key=lambda x: (x["prefix"], x["peer"]))
    for row in items:
        assert isinstance(row.get("prefix"), str)
        assert isinstance(row.get("peer"), str)
        assert isinstance(row.get("as_path"), list)
        assert row["as_path"]


def test_foxtrot(tool_output):
    """All bundles present and leak ledger matches the stock-versus-corrected divergences."""
    fib, leaks = tool_output
    assert set(fib) == {"alpha", "bravo", "charlie", "delta", "india", "juliet"}
    assert leaks == LEAKS_GT
