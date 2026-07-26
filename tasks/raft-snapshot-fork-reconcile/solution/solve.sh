#!/bin/bash
set -euo pipefail

test -d /app/config/l7
test -x /app/bin/ctl
test -d /app/lane
mkdir -p /output /app/ops/staging

read -r ANCHOR CUTOFF < <(
python3 <<'PY'
import json
from pathlib import Path

data = Path("/app/data")


def discover_anchor() -> int:
    anchor = None
    for line in (data / "manifests/tier_b.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("ns") != "events":
            continue
        if 99 in rec.get("stripes", []):
            break
        anchor = int(rec["gen"])
    if anchor is None:
        raise SystemExit("could not derive anchor generation from tier_b journal")
    return anchor


def discover_barrier() -> int:
    tombstone_seq = None
    for name in ("seg_001.bin", "seg_002.bin"):
        blob = (data / "wal" / name).read_bytes()
        if blob[:4] != b"WLOG":
            raise SystemExit(f"bad wal magic in {name}")
        off = 4
        while off + 11 <= len(blob):
            seq = int.from_bytes(blob[off : off + 8], "little")
            off += 8
            op = blob[off]
            off += 1
            key_len = int.from_bytes(blob[off : off + 2], "little")
            off += 2
            key = blob[off : off + key_len].decode()
            off += key_len
            off += 8
            if op == 1 and key == "marker_zulu":
                tombstone_seq = seq
    if tombstone_seq is None:
        raise SystemExit("could not locate tombstone cutoff in wal segments")
    return tombstone_seq


print(discover_anchor(), discover_barrier())
PY
)

sed -i "s/^tier_c = .*/tier_c = ${ANCHOR}/" /app/config/l7/k9.toml
sed -i "s/^journal_pin = .*/journal_pin = ${ANCHOR}/" /app/config/l7/k9.toml
sed -i "s/^head_floor = .*/head_floor = ${ANCHOR}/" /app/config/l7/k9.toml
sed -i 's/^roll_ready = .*/roll_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml
sed -i 's/^sync_token = .*/sync_token = "armed"/' /app/config/l7/k9.toml

sed -i "s/^seq_cutoff = .*/seq_cutoff = ${CUTOFF}/" /app/config/l7/m2.toml
sed -i "s/^wal_floor = .*/wal_floor = ${CUTOFF}/" /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^tomb_scan = .*/tomb_scan = true/' /app/config/l7/m2.toml

sed -i 's/^phases = .*/phases = ["roll", "barrier", "rebuild"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml
sed -i 's/^workflow_note = .*/workflow_note = "live"/' /app/config/l7/p7.toml

cp /solution/fixtures/branch.go /app/lane/internal/m7/branch.go

(cd /app/lane && go build -trimpath -ldflags="-s -w" -o /app/bin/lane ./cmd/lane)

for phase in roll barrier rebuild; do
  case "${phase}" in
    roll)
      /app/bin/ctl roll --ks events
      ;;
    barrier)
      /app/bin/ctl barrier
      ;;
    rebuild)
      /app/bin/ctl rebuild --ks events
      ;;
    *)
      echo "unknown phase ${phase}" >&2
      exit 1
      ;;
  esac
done

/app/bin/ctl report --out /output/fork-report.json
/app/bin/lane emit --out /output/fork-report.json

probe_alpha=$(/app/bin/ctl query point --ks events --key alpha --ts 550)
probe_marker=$(/app/bin/ctl query point --ks events --key marker_zulu --ts 550)
echo "${probe_alpha}" | grep -q '"found":true'
echo "${probe_marker}" | grep -q '"found":false'

lane_head=$(/app/bin/lane head)
runtime_gen=$(python3 -c "import json; print(json.load(open('/app/data/state/runtime.json'))['active_gen'])")
test "${lane_head}" = "${runtime_gen}"

status_json=$(/app/bin/ctl status)
restored_gen=$(python3 -c "import json; print(json.load(open('/output/fork-report.json'))['restored_generation'])")
ceiling_gen=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['ceiling_gen'])" "${status_json}")
test "${restored_gen}" -le "${ceiling_gen}"

echo "complete" > /app/ops/staging/workflow.complete
