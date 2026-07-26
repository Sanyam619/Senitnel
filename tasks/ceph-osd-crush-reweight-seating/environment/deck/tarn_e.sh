#!/bin/bash
set -euo pipefail
tarn_e() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local out="${SD_REPORT:-/output/crush-seat.json}"
  local tmp="${out}.tmp"
  local g_live f n node wm sep row name size pg flag ok

  g_live=$(cat "$sv/state/gen.live" 2>/dev/null || echo 0)
  ok=false
  if /usr/local/bin/cephhealth 2>/dev/null | grep -q 'HEALTH_OK'; then
    ok=true
  fi

  {
    printf '{\n'
    printf '  "schema_tag": "crush-seat-v1",\n'
    printf '  "pass_stamp": %s,\n' "$(date +%s%N)"
    printf '  "osds": [\n'
    sep=""
    for f in $(ls "$sx"/reweight.d/osd.*.conf | sort -t. -k2 -n); do
      n=${f##*/osd.}
      n=${n%.conf}
      wm=$(sed -n 's/^reweight_milli = \([0-9]*\)$/\1/p' "$f")
      node=$(cat "$sv/state/spine.${n}.node" 2>/dev/null || echo "unknown")
      local marked=false
      [[ -f "$sv/state/knot.${n}.flag" ]] && marked=true
      printf '%s' "$sep"
      printf '    {"id": %s, "host": "%s", "weight": %s, "in": %s, "up": true, "generation": %s}' \
        "$n" "$node" "$(awk -v m="$wm" 'BEGIN{printf "%g", m/1000}')" \
        "$([[ "$marked" == true ]] && echo false || echo true)" "$g_live"
      sep=$',\n'
    done
    printf '\n  ],\n'
    printf '  "pools": [\n'
    sep=""
    name=""
    for f in $(ls "$sx"/pools.d/*.conf | LC_ALL=C sort); do
      while IFS= read -r row || [[ -n "${row:-}" ]]; do
        if [[ "$row" =~ ^\[pool\ \"([a-z-]+)\"\]$ ]]; then
          name="${BASH_REMATCH[1]}"
          size=""
          pg=""
          flag=false
        elif [[ "$row" =~ ^size\ =\ ([0-9]+)$ ]]; then
          size="${BASH_REMATCH[1]}"
        elif [[ "$row" =~ ^pg_num\ =\ ([0-9]+)$ ]]; then
          pg="${BASH_REMATCH[1]}"
        elif [[ "$row" =~ ^state\ =\ (.*)$ ]]; then
          [[ "${BASH_REMATCH[1]}" == "degraded" ]] && flag=true
          printf '%s' "$sep"
          printf '    {"name": "%s", "size": %s, "pg_num": %s, "degraded": %s}' \
            "$name" "$size" "$pg" "$flag"
          sep=$',\n'
        fi
      done <"$f"
    done
    printf '\n  ],\n'
    printf '  "seat_ok": %s\n' "$ok"
    printf '}\n'
  } >"$tmp"
  mv "$tmp" "$out"
}
tarn_e
