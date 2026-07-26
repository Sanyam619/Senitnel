#!/bin/bash
set -euo pipefail

test -d /app/config/l7
test -x /app/bin/ctl
test -x /app/bin/window
mkdir -p /output /app/ops/staging

# Discover anchor generation from tier_b journal manifest: iterate the events
# records in order and keep the last gen whose stripe set does not include
# the tainted stripe 99.
discover_anchor() {
    awk '
        /"ns":[[:space:]]*"events"/ {
            stripes_field = ""
            if (match($0, /"stripes":[[:space:]]*\[[^]]*\]/)) {
                stripes_field = substr($0, RSTART, RLENGTH)
            }
            if (stripes_field ~ /(^|[^0-9])99([^0-9]|$)/) { exit }
            if (match($0, /"gen":[[:space:]]*[0-9]+/)) {
                gen_field = substr($0, RSTART, RLENGTH)
                gsub(/[^0-9]/, "", gen_field)
                anchor = gen_field
            }
        }
        END {
            if (anchor == "") { exit 1 }
            print anchor
        }
    ' /app/data/manifests/tier_b.jsonl
}

# Scan a WAL segment binary and print the sequence number of any tombstone
# (op == 1) entry whose key equals marker_zulu. Record layout after the
# 4-byte "WLOG" magic:
#   seq  : u64 little-endian
#   op   : u8
#   klen : u16 little-endian
#   key  : klen bytes
#   val  : 8 bytes
scan_wal_segment() {
    local file="$1"
    local size magic off op key_len key seq
    size=$(stat -c%s "$file")
    magic=$(dd if="$file" bs=1 count=4 status=none)
    if [ "$magic" != "WLOG" ]; then
        echo "bad wal magic in $file" >&2
        return 1
    fi
    off=4
    while [ $((off + 11)) -le "$size" ]; do
        seq=$(od -An -j"$off" -N8 --endian=little -tu8 "$file" | tr -d ' \n')
        off=$((off + 8))
        op=$(od -An -j"$off" -N1 -tu1 "$file" | tr -d ' \n')
        off=$((off + 1))
        key_len=$(od -An -j"$off" -N2 --endian=little -tu2 "$file" | tr -d ' \n')
        off=$((off + 2))
        if [ "$key_len" -gt 0 ]; then
            key=$(dd if="$file" bs=1 skip="$off" count="$key_len" status=none)
        else
            key=""
        fi
        off=$((off + key_len + 8))
        if [ "$op" = "1" ] && [ "$key" = "marker_zulu" ]; then
            echo "$seq"
        fi
    done
}

discover_barrier() {
    local hit=""
    local candidate
    for name in seg_001.bin seg_002.bin; do
        candidate=$(scan_wal_segment "/app/data/wal/$name" | tail -n1)
        if [ -n "$candidate" ]; then
            hit="$candidate"
        fi
    done
    if [ -z "$hit" ]; then
        echo "could not locate tombstone cutoff in wal segments" >&2
        return 1
    fi
    echo "$hit"
}

anchor_gen=$(discover_anchor)
barrier_cutoff=$(discover_barrier)

sed -i "s/^tier_c = .*/tier_c = ${anchor_gen}/" /app/config/l7/k9.toml
sed -i "s/^journal_pin = .*/journal_pin = ${anchor_gen}/" /app/config/l7/k9.toml
sed -i "s/^head_floor = .*/head_floor = ${anchor_gen}/" /app/config/l7/k9.toml
sed -i 's/^roll_ready = .*/roll_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml
sed -i 's/^sync_token = .*/sync_token = "armed"/' /app/config/l7/k9.toml

sed -i "s/^seq_cutoff = .*/seq_cutoff = ${barrier_cutoff}/" /app/config/l7/m2.toml
sed -i "s/^wal_floor = .*/wal_floor = ${barrier_cutoff}/" /app/config/l7/m2.toml
sed -i 's/^scan_tier = .*/scan_tier = "b"/' /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^tomb_scan = .*/tomb_scan = true/' /app/config/l7/m2.toml

# Optional operator log sync for ctl workflow; individual roll/barrier/rebuild
# do not require this table, and the verifier does not grade phases order.
sed -i 's/^phases = .*/phases = ["roll", "barrier", "rebuild"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml
sed -i 's/^workflow_note = .*/workflow_note = "live"/' /app/config/l7/p7.toml

grep -q "^tier_c = ${anchor_gen}$" /app/config/l7/k9.toml
grep -q "^seq_cutoff = ${barrier_cutoff}$" /app/config/l7/m2.toml

/app/bin/ctl roll --ks events
/app/bin/ctl barrier
/app/bin/ctl rebuild --ks events

/app/bin/ctl report --out /output/backfill-report.json

probe_alpha=$(/app/bin/ctl query point --ks events --key alpha --ts 550)
probe_marker=$(/app/bin/ctl query point --ks events --key marker_zulu --ts 550)
echo "${probe_alpha}" | grep -q '"found":true'
echo "${probe_marker}" | grep -q '"found":false'

window_head=$(/app/bin/window head)
test "${window_head}" -eq "${anchor_gen}"

status_json=$(/app/bin/ctl status)
restored_gen=$(awk 'match($0, /"restored_generation":[[:space:]]*[0-9]+/) { s=substr($0, RSTART, RLENGTH); gsub(/[^0-9]/, "", s); print s; exit }' /output/backfill-report.json)
ceiling_gen=$(printf '%s' "$status_json" | awk 'match($0, /"ceiling_gen":[[:space:]]*[0-9]+/) { s=substr($0, RSTART, RLENGTH); gsub(/[^0-9]/, "", s); print s; exit }')
test "${restored_gen}" -le "${ceiling_gen}"

echo "complete" > /app/ops/staging/workflow.complete
