#!/usr/bin/env bash
set -uo pipefail

if [ ! -x /opt/rly/bin/fwreplay ] || [ ! -x /opt/rly/bin/sealmake ] || [ ! -x /opt/rly/bin/floorcheck ]; then
  echo "missing lab tools" >&2
  exit 1
fi

cd /data

cat > config/publish_lane.toml <<'PROFILE'
lane = "floor"
trace = "primary"
walk = "event_ordinal"
PROFILE

cat > config/rebind_runbook.toml <<'RUNBOOK'
# publish lane rebind notes
phase = "floor"
tooling = ["fwreplay", "sealmake", "floorcheck", "benchcheck", "logscan"]
matrix = "/opt/rly/config/matrix.yaml"
publish = "/opt/rly/config/publish_lane.toml"
trace_root = "/data/traces"
blob_root = "/data/blobs"
bundle_out = "/output/attestation-bundle.json"
verdict_out = "/output/gate-verdict.json"

[publish]
lane = "floor"
trace = "primary"
walk = "event_ordinal"

[inspect]
command = "logscan --traces /data/traces"

[refresh]
command = "fwreplay"

[seal]
command = "sealmake"

[verify]
command = "floorcheck"
lane = "floor"
result = "accept"

[state]
path = "/data/rly/chip-state.json"
reset_script = "/opt/rly/scripts/reset-primary.sh"

[paths]
anchor = "/data/fixtures/anchor-blobs"
keys = "/opt/rly/keys"

[ordering]
first = "fwreplay"
second = "sealmake"
third = "floorcheck"
RUNBOOK

bash /opt/rly/scripts/reset-primary.sh

rm -f /output/attestation-bundle.json /output/gate-verdict.json

/opt/rly/bin/logscan --traces /data/traces >/dev/null

/opt/rly/bin/fwreplay --traces /data/traces --state /data/rly/chip-state.json
/opt/rly/bin/sealmake --out /output/attestation-bundle.json
/opt/rly/bin/floorcheck --bundle /output/attestation-bundle.json --verdict /output/gate-verdict.json

python3 - <<'PY'
import json
from pathlib import Path

bundle = json.loads(Path("/output/attestation-bundle.json").read_text())
assert bundle.get("version") == 1
for bank in ("0", "1", "7", "8"):
    assert bank in bundle.get("registers", {}), bank
verdict = json.loads(Path("/output/gate-verdict.json").read_text())
assert verdict.get("result") == "accept"
assert verdict.get("lane") == "floor"
PY

echo "rebind complete"
