#!/usr/bin/env python3
from pathlib import Path

TASK = Path("/Users/sanyamgupta/Desktop/TERMINUS/tasks/landlock-seccomp-notify-admission-mesh")

(TASK / "tests/test_outputs.py").write_text(
    '''"""Behavioral checks for the admission quarantine ledger."""

import json
import subprocess
from pathlib import Path

APP = Path("/app")
LEDGER = Path("/output/admit-ledger.json")
QUAR = Path("/output/quarantine.json")
RUNTIME = APP / "data" / "state" / "runtime.json"
SCEN_DIR = APP / "data" / "scenarios"
JOURNAL = APP / "data" / "seating" / "canon.journal"
DURABLE = APP / "data" / "roots" / "durable.map"
SURFCHECK_SCRIPT = APP / "scripts" / "surfcheck"
RUN_ADMIT_SCRIPT = APP / "scripts" / "run-admit.sh"
FRAMECHECK = APP / "bin" / "framecheck"

RUN_ADMIT = "/app/scripts/run-admit.sh"
MESH_REFRESH = "/app/scripts/mesh-refresh.sh"
SURFCHECK = "/app/bin/surfcheck"

EXPECTED = {
    "m2": ("job-m2", "accept", "ok_admit"),
    "w2": ("job-w2", "accept", "ok_admit"),
    "k9": ("job-k9", "quarantine", "path_drift"),
    "n4": ("job-n4", "quarantine", "fd_stale"),
    "p7": ("job-p7", "quarantine", "notify_skew"),
    "q3": ("job-q3", "quarantine", "epoch_revoke"),
    "r6": ("job-r6", "accept", "ok_admit"),
    "t1": ("job-t1", "accept", "ok_admit"),
    "u8": ("job-u8", "accept", "ok_admit"),
    "v5": ("job-v5", "accept", "ok_admit"),
    "x2": ("job-x2", "accept", "ok_admit"),
    "h4": ("job-h4", "quarantine", "path_drift"),
    "s9": ("job-s9", "quarantine", "replay"),
}

_FORBIDDEN_SNAP = None


def _journal_map():
    """Agent-visible seating authority — same source tests and solvers use."""
    out = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        alias = row["alias"]
        if "canon" in row:
            out[alias] = row["canon"]
        elif "via" in row:
            out[alias] = row["via"]
    return out


def _materialize_durable_from_journal():
    m = _journal_map()
    lines = ["# durable seating recovered from sealed seating journal"]
    for k in sorted(m):
        lines.append(f"{k}={m[k]}")
    return "\\n".join(lines) + "\\n"


def _snapshot_bytes(path):
    return path.read_bytes()


def _snapshot_tree(root):
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(APP))] = path.read_bytes()
    return out


def _forbidden_snap():
    global _FORBIDDEN_SNAP
    if _FORBIDDEN_SNAP is None:
        _FORBIDDEN_SNAP = (
            _snapshot_tree(SCEN_DIR),
            _snapshot_bytes(SURFCHECK_SCRIPT),
            _snapshot_bytes(RUN_ADMIT_SCRIPT),
            _snapshot_bytes(FRAMECHECK),
            _snapshot_bytes(JOURNAL),
        )
    return _FORBIDDEN_SNAP


def _assert_prohibited_untouched():
    scenarios, surf, run_bytes, gate, journal = _forbidden_snap()
    assert _snapshot_tree(SCEN_DIR) == scenarios
    assert _snapshot_bytes(SURFCHECK_SCRIPT) == surf
    assert _snapshot_bytes(RUN_ADMIT_SCRIPT) == run_bytes
    assert _snapshot_bytes(FRAMECHECK) == gate
    assert _snapshot_bytes(JOURNAL) == journal


def _reset_runtime():
    RUNTIME.write_text('{"epoch": 7}\\n')


def _restore_durable():
    DURABLE.write_text(_materialize_durable_from_journal())


def _run_admit():
    _restore_durable()
    _reset_runtime()
    subprocess.run(
        [RUN_ADMIT],
        check=True,
        cwd="/app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _assert_prohibited_untouched()
    return _load()


def _load():
    return json.loads(LEDGER.read_text())


def _cases(data):
    return {c["id"]: c for c in data["cases"]}


def _runtime_epoch():
    return json.loads(RUNTIME.read_text())["epoch"]


def _assert_row(data, scenario_id):
    row = _cases(data)[scenario_id]
    job_id, decision, reason_code = EXPECTED[scenario_id]
    assert row["job_id"] == job_id
    assert row["decision"] == decision
    assert row["reason_code"] == reason_code


def _surf_lines():
    proc = subprocess.run(
        [SURFCHECK],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = {}
    for line in proc.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            lines[parts[0]] = parts[1]
    return lines


def test_m8_obsidian():
    data = _run_admit()
    _assert_row(data, "w2")


def test_k3_garnet():
    data = _run_admit()
    _assert_row(data, "k9")
    assert _cases(data)["k9"]["reason_code"] != "ok_admit"


def test_n4_topaz():
    data = _run_admit()
    _assert_row(data, "n4")
    assert _cases(data)["n4"]["reason_code"] != "path_drift"


def test_p7_onyx():
    data = _run_admit()
    _assert_row(data, "p7")
    assert _cases(data)["p7"]["decision"] == "quarantine"


def test_q7_amber():
    data = _run_admit()
    _assert_row(data, "q3")
    assert _cases(data)["q3"]["reason_code"] != "notify_skew"


def test_r1_zircon():
    d1 = _run_admit()
    assert d1["schema_version"] == "admit-mesh-1"
    assert d1["reload_epoch"] == 7
    assert _runtime_epoch() == 7
    m1 = {c["id"]: (c["decision"], c["reason_code"]) for c in d1["cases"]}
    durable_before = DURABLE.read_bytes()

    subprocess.run(
        [MESH_REFRESH],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        [RUN_ADMIT],
        check=True,
        cwd="/app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _assert_prohibited_untouched()
    d2 = _load()
    m2 = {c["id"]: (c["decision"], c["reason_code"]) for c in d2["cases"]}
    assert m1 == m2
    assert d2["reload_epoch"] == d1["reload_epoch"] == 7
    assert _runtime_epoch() == 7
    assert DURABLE.read_bytes() == durable_before
    for sid in EXPECTED:
        _assert_row(d2, sid)


def test_t6_jade():
    data = _run_admit()
    _assert_row(data, "t1")
    _assert_row(data, "k9")
    surf = _surf_lines()
    assert surf.get("k9") == "OK"
    assert _cases(data)["k9"]["decision"] == "quarantine"


def test_u2_quartz():
    data = _run_admit()
    _assert_row(data, "u8")
    assert _cases(data)["u8"]["reason_code"] != "notify_skew"


def test_v5_spinel():
    data = _run_admit()
    _assert_row(data, "v5")
    jm = _journal_map()
    assert jm["/data/alias/v5/blob"] == "/data/bridge/v5/blob"
    assert jm["/data/bridge/v5/blob"] == "/data/vault/v5/blob"


def test_x2_beryl():
    data = _run_admit()
    _assert_row(data, "x2")
    assert _cases(data)["x2"]["reason_code"] != "fd_stale"


def test_h6_jadeite():
    data = _run_admit()
    _assert_row(data, "h4")
    assert _cases(data)["h4"]["reason_code"] != "notify_skew"


def test_w9_coral():
    data = _run_admit()
    _assert_row(data, "r6")
    assert _cases(data)["r6"]["reason_code"] != "epoch_revoke"


def test_y4_opal():
    data = _run_admit()
    assert data["schema_version"] == "admit-mesh-1"
    surf = _surf_lines()
    assert surf.get("k9") == "OK"
    assert surf.get("h4") == "OK"
    assert _cases(data)["k9"]["decision"] == "quarantine"
    assert _cases(data)["h4"]["decision"] == "quarantine"
    assert _cases(data)["m2"]["decision"] == "accept"
    assert _cases(data)["s9"]["reason_code"] == "replay"
    q = json.loads(QUAR.read_text())
    assert q["version"] == 1
    reasons = {r["reason"] for r in q["rows"]}
    assert "replay" in reasons
    assert "path_drift" in reasons


def test_z2_fluorite():
    _restore_durable()
    _reset_runtime()
    subprocess.run(["make"], check=True, cwd="/app", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(
        [RUN_ADMIT],
        check=True,
        cwd="/app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _assert_prohibited_untouched()
    data = _load()
    for sid in EXPECTED:
        _assert_row(data, sid)


def test_a1_framecheck():
    seed = json.loads((APP / "data/fixtures/seed.json").read_text())["seed_hex"]
    scen = json.loads((SCEN_DIR / "m2.json").read_text())
    frame = {
        "seed_hex": seed,
        "epoch": scen["epoch"],
        "lane": scen["lane"],
        "strand": 61,
        "payload_hex": scen["payload_hex"],
        "check": scen["check"],
    }
    path = Path("/tmp/frame_m2.json")
    path.write_text(json.dumps(frame))
    proc = subprocess.run(
        [str(FRAMECHECK), "--frame", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert "ok" in proc.stdout


def test_b2_journal_authority():
    jm = _journal_map()
    assert jm["/data/alias/k9/blob"].startswith("/data/outside/")
    data = _run_admit()
    _assert_row(data, "k9")
'''
)

# Fix accidental double-escaped newlines in the test file content above
text = (TASK / "tests/test_outputs.py").read_text()
text = text.replace('"\\n".join', '"\\n".join')  # noop guard
# The write used \\n in join/runtime — convert to real \n escapes for Python source
text = text.replace("'\\n'.join(lines) + '\\n'", "'\\n'.join(lines) + '\\n'")
# Actually the file has literal backslash-n from the triple-quoted write with \\n
text = text.replace("return \"\\\\n\".join(lines) + \"\\\\n\"", "return \"\\n\".join(lines) + \"\\n\"")
text = text.replace("RUNTIME.write_text('{\\\"epoch\\\": 7}\\\\n')", "RUNTIME.write_text('{\\\"epoch\\\": 7}\\n')")
# Simpler: rewrite the two helper bodies
text = text.replace(
    'return "\\n".join(lines) + "\\n"',
    'return "\\n".join(lines) + "\\n"',
)
(TASK / "tests/test_outputs.py").write_text(text)

# Check what we actually have
sample = (TASK / "tests/test_outputs.py").read_text()
print("join line:", [ln for ln in sample.splitlines() if "join(lines)" in ln])
print("runtime line:", [ln for ln in sample.splitlines() if "RUNTIME.write" in ln])

solve = r'''#!/bin/bash
set -euo pipefail

cat > /app/qx/internal/seat_k.go <<'EOF'
package internal

var SeatMode = "durable"

var SeatAllow = "/data/vault/"
EOF

cat > /app/qx/internal/band_k.go <<'EOF'
package internal

var BandLo int64 = 4

var BandHi int64 = 9
EOF

cat > /app/qx/internal/bind_y.go <<'EOF'
package internal

func bind_y(dir string, lst string) (mapPath string, allowPath string, allowInline string, useJournal bool) {
	_ = lst
	if SeatMode == "durable" {
		return dir + "/durable.map", "", SeatAllow, true
	}
	return dir + "/live.map", "/app/data/surface/allow.list", "", false
}
EOF

cat > /app/rz/mat_q.c <<'EOF'
#include <stdint.h>
#include <string.h>

#include "mat_q.h"

static unsigned char rotl8(unsigned char x, unsigned n)
{
    n %= 8u;
    return (unsigned char)((x << n) | (x >> (8u - n)));
}

void mat_q(const unsigned char *seed, size_t n, unsigned epoch,
           unsigned lane, unsigned strand, unsigned char *out)
{
    size_t i;
    unsigned char elo = (unsigned char)(epoch & 0xffu);
    for (i = 0; i < n; i++) {
        unsigned char mix = rotl8(elo, (unsigned)((i % 5) + 1));
        unsigned char stride = (unsigned char)((5u * (unsigned)i + 1u) & 0xffu);
        out[i] = (unsigned char)(seed[i] ^ mix ^ stride ^ (unsigned char)strand ^ (unsigned char)lane);
    }
}
EOF

cat > /app/rz/knit_m.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "knit_m.h"

int knit_m(const unsigned char *payload, size_t n,
           const unsigned char *material, size_t mlen,
           unsigned expect)
{
    unsigned sum = 0;
    size_t i;
    if (mlen == 0) {
        return 0;
    }
    for (i = 0; i < n; i++) {
        sum = (sum + (payload[i] ^ material[i % mlen])) & 0xffu;
    }
    return sum == (expect & 0xffu);
}
EOF

cat > /app/scripts/mesh-refresh.sh <<'EOF'
#!/bin/bash
set -euo pipefail
cp /app/data/roots/live.map /app/data/roots/live.map.refresh
mv /app/data/roots/live.map.refresh /app/data/roots/live.map
EOF
chmod +x /app/scripts/mesh-refresh.sh

python3 - <<'PY'
import json
from pathlib import Path
journal = Path("/app/data/seating/canon.journal")
out = ["# durable seating recovered from sealed seating journal"]
m = {}
for line in journal.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    row = json.loads(line)
    alias = row["alias"]
    if "canon" in row:
        m[alias] = row["canon"]
    elif "via" in row:
        m[alias] = row["via"]
for k in sorted(m):
    out.append(f"{k}={m[k]}")
Path("/app/data/roots/durable.map").write_text("\n".join(out) + "\n")
PY

cd /app
make
/app/scripts/run-admit.sh
'''
(TASK / "solution/solve.sh").write_text(solve)
(TASK / "solution/solve.sh").chmod(0o755)
print("solve ok", (TASK / "solution/solve.sh").stat().st_size)
