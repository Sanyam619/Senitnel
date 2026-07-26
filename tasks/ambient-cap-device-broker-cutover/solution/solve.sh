#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

for tool in topsurf nsprobe laneapply nodeseat racepulse ledgerout; do
  if [ ! -x "/opt/broker/bin/$tool" ]; then
    echo "missing helper: $tool" >&2
    exit 1
  fi
done

if ! command -v gcc >/dev/null 2>&1 || ! command -v make >/dev/null 2>&1; then
  echo "missing rebuild toolchain (gcc/make)" >&2
  exit 1
fi

rm -f /output/broker-cutover.json

echo "== reading active profile =="
profile_name=$(grep -oP 'active_profile\s*=\s*"\K[^"]+' /opt/broker/config/lab.toml)
profile_conf="/opt/broker/config/${profile_name}-caps.conf"
correct_caps=$(grep -oP 'capability_boundary\s*=\s*"\K[^"]+' "$profile_conf")
echo "profile=$profile_name caps=$correct_caps"

echo "== fixing bounding from profile =="
echo -n "$correct_caps" > /data/lab/caps/bounding

cat > /app/lane/apply_lane_a.c <<'EOF'
#include "apply_lane_a.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>

static int private_devices_on(void) {
    char u[4096];
    if (read_text(UNIT_LIVE, u, sizeof(u)) == 0) {
        if (strstr(u, "PrivateDevices=yes") != NULL) return 1;
    }
    if (read_text(UNIT_DROPIN, u, sizeof(u)) == 0) {
        if (strstr(u, "PrivateDevices=yes") != NULL) return 1;
    }
    return 0;
}

int apply_lane_a(const char *a, const char *b) {
    (void)b;
    const char *root = (a && a[0]) ? a : LAB_ROOT;
    char p0[512], p1[512], p2[512];
    snprintf(p0, sizeof(p0), "%s/caps/bounding", root);
    snprintf(p1, sizeof(p1), "%s/caps/ambient", root);
    snprintf(p2, sizeof(p2), "%s/caps/effective", root);

    if (private_devices_on()) {
        write_text(p1, "");
        write_text(p2, "");
        return 0;
    }

    char bound[512];
    if (read_text(p0, bound, sizeof(bound)) != 0) return -1;
    if (bound[0] == 0) return -1;
    if (write_text(p1, bound) != 0) return -1;
    if (write_text(p2, bound) != 0) return -1;
    return 0;
}
EOF

cat > /app/seat/seat_slot_b.c <<'EOF'
#define _DEFAULT_SOURCE
#include "seat_slot_b.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int seat_slot_b(const char *a, const char *b, const char *c) {
    const char *src = (a && a[0]) ? a : HOST_DEV;
    const char *dst = (b && b[0]) ? b : BROKER_DEV;
    const char *csv = (c && c[0]) ? c : "dev-alpha,dev-beta,dev-gamma";
    char buf[256];
    snprintf(buf, sizeof(buf), "%s", csv);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
        char s[512], d[512], st[512];
        snprintf(s, sizeof(s), "%s/%s", src, tok);
        snprintf(d, sizeof(d), "%s/%s", dst, tok);
        snprintf(st, sizeof(st), "%s/%s", HOST_STALE, tok);
        ensure_dir(dst);
        if (!file_exists(s) && !file_exists(d)) return -1;
        if (file_exists(s)) {
            char body[256];
            if (read_text(s, body, sizeof(body)) != 0) return -1;
            if (write_text(d, body) != 0) return -1;
            unlink(s);
        }
        if (file_exists(st)) unlink(st);
    }
    ensure_dir("/data/lab/identity");
    if (write_text(MNT_ID, "broker") != 0) return -1;
    return 0;
}
EOF

cat > /app/roll/emit_rollup_c.c <<'EOF'
#include "emit_rollup_c.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>

static int rewrite_private_no(const char *path) {
    char buf[8192];
    if (read_text(path, buf, sizeof(buf)) != 0) return -1;
    char out[8192];
    const char *p = buf;
    size_t o = 0;
    int saw_priv = 0;
    while (*p && o + 1 < sizeof(out)) {
        if (strncmp(p, "PrivateDevices=yes", 18) == 0) {
            const char *rep = "PrivateDevices=no";
            size_t n = strlen(rep);
            memcpy(out + o, rep, n);
            o += n;
            p += 18;
            saw_priv = 1;
            continue;
        }
        if (strncmp(p, "PrivateDevices=no", 17) == 0) {
            saw_priv = 1;
        }
        out[o++] = *p++;
    }
    out[o] = 0;
    if (!saw_priv) {
        if (o + 20 < sizeof(out)) {
            memcpy(out + o, "\nPrivateDevices=no\n", 19);
            o += 19;
            out[o] = 0;
        }
    }
    return write_text(path, out);
}

int emit_rollup_c(const char *a, const char *b) {
    if (!a) return -1;
    if (strcmp(a, "fold") == 0) {
        if (rewrite_private_no(UNIT_LIVE) != 0) return -1;
        if (rewrite_private_no(UNIT_DROPIN) != 0) return -1;
        char live[8192];
        if (read_text(UNIT_LIVE, live, sizeof(live)) != 0) return -1;
        if (strstr(live, "DeviceAllow=") == NULL) return -1;
        if (strstr(live, "PrivateDevices=yes") != NULL) return -1;
        if (strstr(live, "PrivateDevices=no") == NULL) return -1;
        char drop[8192];
        if (read_text(UNIT_DROPIN, drop, sizeof(drop)) != 0) return -1;
        if (strstr(drop, "PrivateDevices=yes") != NULL) return -1;
        if (strstr(drop, "PrivateDevices=no") == NULL) return -1;
        return 0;
    }
    if (strcmp(a, "emit") == 0) {
        char amb[512], bound[512], mnt[64];
        if (read_text(CAP_AMB, amb, sizeof(amb)) != 0) amb[0] = 0;
        if (read_text(CAP_BOUND, bound, sizeof(bound)) != 0) return -1;
        if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0) snprintf(mnt, sizeof(mnt), "host");

        const char *names[] = {"dev-alpha", "dev-beta", "dev-gamma"};
        int stale_ok = 1;
        for (int i = 0; i < 3; i++) {
            char sp[512], hp[512], bp[512];
            snprintf(sp, sizeof(sp), "%s/%s", HOST_STALE, names[i]);
            snprintf(hp, sizeof(hp), "%s/%s", HOST_DEV, names[i]);
            snprintf(bp, sizeof(bp), "%s/%s", BROKER_DEV, names[i]);
            if (file_exists(sp)) stale_ok = 0;
            if (file_exists(hp) || !file_exists(bp)) stale_ok = 0;
        }
        if (strcmp(mnt, "broker") != 0) stale_ok = 0;

        char body[4096];
        int n = snprintf(
            body,
            sizeof(body),
            "{\n"
            "  \"version\": 1,\n"
            "  \"devices\": [\n"
            "    {\"name\": \"dev-alpha\", \"mount_ns\": \"%s\", \"ambient_set\": \"%s\", \"bounding_set\": \"%s\", \"stale_cleared\": %s},\n"
            "    {\"name\": \"dev-beta\", \"mount_ns\": \"%s\", \"ambient_set\": \"%s\", \"bounding_set\": \"%s\", \"stale_cleared\": %s},\n"
            "    {\"name\": \"dev-gamma\", \"mount_ns\": \"%s\", \"ambient_set\": \"%s\", \"bounding_set\": \"%s\", \"stale_cleared\": %s}\n"
            "  ]\n"
            "}\n",
            mnt, amb, bound, stale_ok ? "true" : "false",
            mnt, amb, bound, stale_ok ? "true" : "false",
            mnt, amb, bound, stale_ok ? "true" : "false");
        if (n < 0 || n >= (int)sizeof(body)) return -1;
        ensure_dir("/output");
        return write_text(b && b[0] ? b : OUT_DEFAULT, body);
    }
    return -1;
}
EOF

echo "== rebuild helpers =="
if ! (cd /app && make clean && make); then
  echo "rebuild failed" >&2
  exit 1
fi
cp -f /app/bin/* /opt/broker/bin/
chmod +x /opt/broker/bin/*

echo "== fold private isolation (live + drop-in) =="
if ! /opt/broker/bin/ledgerout --fold; then
  echo "fold failed" >&2
  exit 1
fi
if grep -q 'PrivateDevices=yes' /data/lab/units/live.service \
   || grep -q 'PrivateDevices=yes' /data/lab/units/live.d/10-private.conf; then
  echo "PrivateDevices still yes" >&2
  exit 1
fi
if ! grep -q 'PrivateDevices=no' /data/lab/units/live.service \
   || ! grep -q 'PrivateDevices=no' /data/lab/units/live.d/10-private.conf; then
  echo "PrivateDevices=no missing" >&2
  exit 1
fi

echo "== ambient handoff =="
if ! /opt/broker/bin/laneapply; then
  echo "laneapply failed" >&2
  exit 1
fi
if [ -z "$(cat /data/lab/caps/ambient)" ] \
   || [ "$(cat /data/lab/caps/ambient)" != "$(cat /data/lab/caps/bounding)" ] \
   || [ "$(cat /data/lab/caps/effective)" != "$(cat /data/lab/caps/bounding)" ]; then
  echo "ambient/effective mismatch" >&2
  exit 1
fi

echo "== seat =="
if ! /opt/broker/bin/nodeseat \
    --src /data/lab/mnt/host/dev \
    --dst /data/lab/mnt/broker/dev \
    --names "dev-alpha,dev-beta,dev-gamma"; then
  echo "nodeseat failed" >&2
  exit 1
fi
for n in dev-alpha dev-beta dev-gamma; do
  [ -f "/data/lab/mnt/broker/dev/$n" ] || { echo "missing $n"; exit 1; }
  [ ! -f "/data/lab/mnt/host/dev/$n" ] || { echo "host still has $n"; exit 1; }
done
[ "$(cat /data/lab/identity/mnt_ns)" = "broker" ] || { echo "mnt_ns wrong"; exit 1; }

echo "== race =="
if ! /opt/broker/bin/racepulse; then
  echo "race dirty" >&2
  exit 1
fi

echo "== emit =="
if ! /opt/broker/bin/ledgerout --emit --out /output/broker-cutover.json; then
  echo "emit failed" >&2
  exit 1
fi
[ -f /output/broker-cutover.json ] || { echo "missing report"; exit 1; }

python3 - /output/broker-cutover.json <<'PY'
import json, re, sys
from pathlib import Path
want = re.search(
    r'capability_boundary\s*=\s*"([^"]+)"',
    Path("/opt/broker/config/fleet-caps.conf").read_text(encoding="utf-8"),
).group(1)
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["version"] == 1
rows = {r["name"]: r for r in payload["devices"]}
for name in ("dev-alpha", "dev-beta", "dev-gamma"):
    r = rows[name]
    assert r["mount_ns"] == "broker"
    assert r["ambient_set"] == r["bounding_set"] == want
    assert r["stale_cleared"] is True
print("oracle ledger ok")
PY

echo "cutover complete"
