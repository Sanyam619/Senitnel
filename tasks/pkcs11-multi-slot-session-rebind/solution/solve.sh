#!/bin/sh
set -eu

mkdir -p /output /logs/agent /tmp /opt/pk11/config/slot_overrides

for tool in findscan slotprobe wireapply holdrun emitout authcheck sealgen; do
  if [ ! -x "/opt/pk11/bin/$tool" ]; then
    echo "missing helper: $tool" >&2
    exit 1
  fi
done

rm -f /output/session-rebind.json

# Collect revoked epochs from the opaque restore journal (tag 01, hex payload).
rvk_epochs=$(
  tr -d '\r' < /data/token/restore.journal \
    | awk -F: '/^01:/ {
        n = length($2)
        v = 0
        for (i = 1; i <= n; i++) {
          c = substr($2, i, 1)
          if (c ~ /[0-9]/) v = v * 16 + c
          else if (c ~ /[a-fA-F]/) v = v * 16 + (index("abcdef", tolower(c)) + 9)
        }
        print v
      }'
)

# Pick highest-epoch live slot that is not revoked.
live_id=$(
  tr -d '\r' < /data/token/inventory.txt | awk -v rvk="$rvk_epochs" '
    BEGIN {
      n = split(rvk, arr, " ")
      for (i = 1; i <= n; i++) if (arr[i] != "") revoked[arr[i]] = 1
      best = -1
      best_id = ""
    }
    /^#/ || NF < 2 { next }
    $2 == "live" {
      ep = (NF >= 3) ? $3 + 0 : 0
      if (ep in revoked) next
      if (ep > best) { best = ep; best_id = $1 }
    }
    END { print best_id }
  '
)

if [ -z "$live_id" ]; then
  echo "no authoritative live slot" >&2
  exit 1
fi
echo "authoritative live: id=$live_id"

global_ttl=$(
  tr -d '\r' < /opt/pk11/config/pin_policy.toml \
    | awk -F= '/^ttl_sec/ { gsub(/ /,"",$2); print $2; exit }'
)
if [ -z "$global_ttl" ]; then
  echo "missing pin_policy ttl" >&2
  exit 1
fi

effective_ttl="$global_ttl"
slot_override="/opt/pk11/config/slot_overrides/${live_id}.toml"
if [ -f "$slot_override" ]; then
  slot_ttl=$(
    tr -d '\r' < "$slot_override" \
      | awk -F= '/^ttl_sec/ { gsub(/ /,"",$2); print $2; exit }'
  )
  if [ -n "$slot_ttl" ] && [ "$slot_ttl" -lt "$effective_ttl" ]; then
    effective_ttl="$slot_ttl"
  fi
fi
echo "effective TTL: $effective_ttl (global=$global_ttl)"

cat > /app/flux/Q7.java <<'EOF'
package flux;

public final class Q7 {
    private Q7() {}

    public static int W_A = 2;
    public static int W_B = 0;
    public static int W_C = 1;
    public static int W_D = 1;
    public static int W_E = 1;
    public static int W_F = 0;
    public static int W_G = 1;
    public static int W_H = 0;
    public static int W_J = 0;
    public static int W_K = 1;
    public static int W_L = 0;
    public static int W_M = 0;
    public static int W_N = 0;
    public static int W_P = 0;
    public static int W_Q = 0;
    public static int W_R = 0;
    public static int W_S = 1;
    public static int W_T = 0;
    public static int W_U = 10;
    public static int W_V = 0;
    public static int W_W = 0;
    public static int W_X = 0;
    public static int W_Y = 0;
    public static int W_Z = 0;

    public static String L_A = "signing-leaf";
    public static String L_B = "wrap-anchor";
    public static String L_C = "live";
}
EOF

cat > /app/nest/M3.java <<'EOF'
package nest;

public final class M3 {
    private M3() {}

    public static int H_A = 1;
    public static int H_B = 1;
    public static int H_C = 0;
    public static int H_D = 1;
    public static int H_E = 1;
    public static int H_F = 1;
    public static int H_G = 86400;
    public static int H_H = 1;
    public static int H_I = 1;
    public static int H_J = 0;
    public static int H_K = 1;
    public static int H_L = 0;
    public static int H_M = 60;
    public static int H_N = 0;
    public static int H_P = 0;
    public static int H_Q = 1;
    public static int H_R = 0;
    public static int H_S = 0;

    public static String HP_A = "/opt/pk11/config/pin_policy.toml";
    public static String HP_B = "/data/token/reload.marker";
    public static String HP_C = "/data/token/session.seal";
    public static String HP_D = "/opt/pk11/config/slot_overrides";
}
EOF

cat > /app/forge/P9.java <<'EOF'
package forge;

public final class P9 {
    private P9() {}

    public static int S_A = 1;
    public static int S_B = 0;
    public static int S_C = 1;
    public static int S_D = 1;
    public static int S_E = 1;
    public static int S_F = 0;
    public static int S_G = 0;
    public static int S_H = 0;
    public static int S_I = 0;
    public static int S_J = 0;
    public static int S_K = 0;
    public static int S_L = 0;
    public static int S_M = 1;
    public static int S_N = 1;
    public static int S_P = 0;
    public static int S_Q = 0;
    public static int S_R = 1;
    public static int S_S = 0;
    public static int S_T = 0;

    public static String SP_A = "/data/token/provider.override";
    public static String SP_B = "/data/token/provider.fallback";
}
EOF

echo "== rebuild helpers =="
if ! (cd /app && make clean && make install); then
  echo "rebuild failed" >&2
  exit 1
fi
cp -f /app/config/*.toml /opt/pk11/config/ 2>/dev/null || true
if [ -d /app/config/slot_overrides ]; then
  mkdir -p /opt/pk11/config/slot_overrides
  cp -f /app/config/slot_overrides/*.toml /opt/pk11/config/slot_overrides/ 2>/dev/null || true
fi
if [ ! -f "/opt/pk11/config/slot_overrides/${live_id}.toml" ]; then
  echo "warning: no slot override for ${live_id}" >&2
fi

echo "== probe before reload =="
/opt/pk11/bin/slotprobe >/tmp/probe-before.txt || true
/opt/pk11/bin/findscan >/tmp/find-before.txt || true

echo "== reload churn =="
sh /opt/pk11/scripts/reload-harness.sh
# Ensure marker exists even if harness was a no-op on a partial state.
touch /data/token/reload.marker

echo "== wire bind =="
if ! /opt/pk11/bin/wireapply; then
  echo "wireapply failed" >&2
  exit 1
fi
bound=$(
  tr -d '\r' < /data/token/provider.txt \
    | awk -F= '/^bound=/ { print $2; exit }'
)
if [ "$bound" != "$live_id" ]; then
  echo "provider bind $bound != live $live_id" >&2
  exit 1
fi

echo "== hold refresh =="
if ! /opt/pk11/bin/holdrun; then
  echo "holdrun failed" >&2
  exit 1
fi
ttl_line=$(
  tr -d '\r' < /data/token/sessions.txt \
    | awk -v id="$live_id" '$1==id { print $3; exit }'
)
if [ -z "$ttl_line" ] || [ "$ttl_line" -gt "$effective_ttl" ]; then
  echo "ttl still stretched: ${ttl_line:-missing} > $effective_ttl" >&2
  exit 1
fi
fresh_line=$(
  tr -d '\r' < /data/token/sessions.txt \
    | awk -v id="$live_id" '$1==id { print $2; exit }'
)
if [ "$fresh_line" != "1" ]; then
  echo "pin marker not refreshed on live id" >&2
  exit 1
fi

echo "== verify seal =="
if [ ! -f /data/token/session.seal ]; then
  echo "seal missing after holdrun; trying sealgen" >&2
  /opt/pk11/bin/sealgen || true
fi
if [ ! -f /data/token/session.seal ]; then
  echo "seal not computed" >&2
  exit 1
fi
seal_content=$(tr -d '[:space:]\r' < /data/token/session.seal)
if [ -z "$seal_content" ] || [ "$seal_content" = "0000000000000000" ]; then
  echo "seal is placeholder or empty" >&2
  exit 1
fi

echo "== stamp emit =="
if ! /opt/pk11/bin/emitout; then
  echo "emitout failed" >&2
  exit 1
fi

echo "== authcheck =="
if ! /opt/pk11/bin/authcheck; then
  echo "authcheck rejected" >&2
  exit 1
fi

/opt/pk11/bin/findscan >/tmp/find-after.txt || true

if [ ! -f /output/session-rebind.json ]; then
  echo "missing ledger" >&2
  exit 1
fi
grep -q '"version"' /output/session-rebind.json
grep -q '"provider_bound"' /output/session-rebind.json
grep -q '"pin_alive"' /output/session-rebind.json
grep -q '"handle_auth"' /output/session-rebind.json

echo "rebind complete"
