#!/bin/bash
# Oracle: bring the placement desk to the durable end-state.
#
# The shipped desk runs against the surface plane: the preflight refreshes
# live sheets from the pre-cutover working sheet on every pass and drops the
# apply receipt; the resolver keeps the oldest row per device and never
# seals; the record scan treats any out row as permanent; the spread pass
# counts devices under every window row; the emitter copies monitor
# annotations and stamps each pass. Rewrite the five stage helpers with the
# real multi-authority logic, select the durable plane, and let the desk
# converge.
set -euo pipefail

SV=/var/lib/ceph/ops
SX=/etc/ceph

# --- Stage 1: preflight gate ------------------------------------------------
cat >/app/ops/kelp_v.sh <<'EOS'
#!/bin/bash
set -euo pipefail
kelp_v() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local plane aim rg rmode ok=0 row n w
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/prefer.toml" | head -n1)
  aim=$(tr -d '[:space:]' <"$sv/gen.aim")
  if [[ "$plane" == "durable" && -f "$sv/state/apply.ok" ]]; then
    rg=$(sed -n 's/^gen=\([0-9]*\)$/\1/p' "$sv/state/apply.ok" | head -n1)
    rmode=$(sed -n 's/^mode=\(.*\)$/\1/p' "$sv/state/apply.ok" | head -n1)
    if [[ "$rg" == "$aim" && "$rmode" == "seal" ]]; then
      ok=1
    fi
  fi
  mkdir -p "$sx/reweight.d"
  if [[ "$plane" == "durable" ]]; then
    if [[ "$ok" -ne 1 ]]; then
      # Refresh live sheets from the packed durable image: the standing row
      # for a device is the newest one, i.e. the last chronological row.
      tail -c +9 "$sv/crushmap.bin" | gzip -dc | awk '
        /^tip / {
          g=""; o=""; w="";
          for (i = 1; i <= NF; i++) {
            if ($i ~ /^gen=/) { g = substr($i, 5) }
            if ($i ~ /^osd=/) { o = substr($i, 5) }
            if ($i ~ /^wm=/)  { w = substr($i, 4) }
          }
          if (o != "") { W[o] = w }
        }
        END { for (o in W) { print o, W[o] } }
      ' | while read -r n w; do
        printf 'reweight_milli = %s\n' "$w" >"$sx/reweight.d/osd.${n}.conf"
      done
    fi
    # A valid receipt on the durable plane means the sheets are settled:
    # leave them and the receipt alone.
  else
    while IFS= read -r row || [[ -n "${row:-}" ]]; do
      [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
      n=${row%% *}
      n=${n#n=}
      w=${row##* }
      w=${w#wm=}
      printf 'reweight_milli = %s\n' "$w" >"$sx/reweight.d/osd.${n}.conf"
    done <"$sv/surface.map"
    rm -f "$sv/state/apply.ok"
  fi
}
kelp_v
EOS

# --- Stage 2: durable resolver + seal receipt --------------------------------
cat >/app/ops/gorse_t.sh <<'EOS'
#!/bin/bash
set -euo pipefail
gorse_t() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local aim magic plane f n want have all=1
  aim=$(tr -d '[:space:]' <"$sv/gen.aim")
  mkdir -p "$sv/state"
  magic=$(head -c 7 "$sv/crushmap.bin")
  if [[ "$magic" != "CRUSHB1" ]]; then
    echo "gorse_t: bad image magic" >&2
    return 1
  fi
  rm -f "$sv/state"/spine.*
  # Resolve the standing row per device from the packed image itself; the
  # newest generation row (last chronological occurrence) wins.
  tail -c +9 "$sv/crushmap.bin" | gzip -dc | awk '
    /^tip / {
      g=""; o=""; h=""; w="";
      for (i = 1; i <= NF; i++) {
        if ($i ~ /^gen=/)  { g = substr($i, 5) }
        if ($i ~ /^osd=/)  { o = substr($i, 5) }
        if ($i ~ /^host=/) { h = substr($i, 6) }
        if ($i ~ /^wm=/)   { w = substr($i, 4) }
      }
      if (o != "") { G[o] = g; H[o] = h; W[o] = w }
    }
    END { for (o in G) { print o, G[o], W[o], H[o] } }
  ' | while read -r n g want have; do
    printf '%s\n' "$g" >"$sv/state/spine.${n}.gen"
    printf '%s\n' "$want" >"$sv/state/spine.${n}.wm"
    printf '%s\n' "$have" >"$sv/state/spine.${n}.node"
  done
  # Seal only when the durable plane is selected and every live sheet
  # already agrees with its standing row.
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/prefer.toml" | head -n1)
  for f in "$sv/state"/spine.*.wm; do
    n=${f##*/spine.}
    n=${n%.wm}
    want=$(tr -d '[:space:]' <"$f")
    have=$(sed -n 's/^reweight_milli = \([0-9]*\)$/\1/p' \
      "$sx/reweight.d/osd.${n}.conf" 2>/dev/null | head -n1)
    if [[ "$have" != "$want" ]]; then
      all=0
    fi
  done
  if [[ "$plane" == "durable" && "$all" -eq 1 ]]; then
    printf 'gen=%s\nmode=seal\n' "$aim" >"$sv/state/apply.ok"
    printf '%s\n' "$aim" >"$sv/state/gen.live"
  fi
}
gorse_t
EOS

# --- Stage 3: record-stream continuity ---------------------------------------
cat >/app/lane/moss_q.sh <<'EOS'
#!/bin/bash
set -euo pipefail
moss_q() {
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local row e n a k
  mkdir -p "$sv/state"
  rm -f "$sv/state"/knot.*.flag
  declare -A last=()
  declare -A when=()
  # Last action per device wins, ordered by epoch; an out followed by a
  # later in leaves the device seated.
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" ]] && continue
    e=$(sed -n 's/.*"epoch": \([0-9]*\).*/\1/p' <<<"$row")
    n=$(sed -n 's/.*"osd": \([0-9]*\).*/\1/p' <<<"$row")
    a=$(sed -n 's/.*"action": "\([a-z]*\)".*/\1/p' <<<"$row")
    [[ -z "$e" || -z "$n" || -z "$a" ]] && continue
    if [[ -z "${when[$n]:-}" ]] || (( e >= when[$n] )); then
      when[$n]=$e
      last[$n]=$a
    fi
  done <"$sv/record.jsonl"
  for k in "${!last[@]}"; do
    if [[ "${last[$k]}" == "out" ]]; then
      printf '1\n' >"$sv/state/knot.${k}.flag"
    fi
  done
}
moss_q
EOS

# --- Stage 4: spread marks ----------------------------------------------------
cat >/app/mast/fern_h.sh <<'EOS'
#!/bin/bash
set -euo pipefail
fern_h() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local now low row node ue f n wm want g name size
  now=$(tr -d '[:space:]' <"$sv/now.mark")
  low=$(tr -d '[:space:]' <"$sv/gen.low")
  declare -A shut=()
  # A window row is active only while until_epoch is strictly greater than
  # the desk clock; expired rows have no effect.
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" ]] && continue
    node=$(sed -n 's/.*"host": "\([a-z0-9-]*\)".*/\1/p' <<<"$row")
    ue=$(sed -n 's/.*"until_epoch": \([0-9]*\).*/\1/p' <<<"$row")
    if [[ -n "$node" && -n "$ue" ]] && (( ue > now )); then
      shut[$node]=1
    fi
  done <"$sv/window.jsonl"
  # Distinct nodes carrying at least one seated device, minus active
  # windows. Seated means the sheet matches the standing row, the standing
  # generation clears the floor (inclusive), and no record flag is set.
  declare -A nodes=()
  for f in "$sx"/reweight.d/osd.*.conf; do
    n=${f##*/osd.}
    n=${n%.conf}
    [[ -f "$sv/state/knot.${n}.flag" ]] && continue
    wm=$(sed -n 's/^reweight_milli = \([0-9]*\)$/\1/p' "$f" | head -n1)
    want=$(cat "$sv/state/spine.${n}.wm" 2>/dev/null || echo "")
    g=$(cat "$sv/state/spine.${n}.gen" 2>/dev/null || echo 0)
    node=$(cat "$sv/state/spine.${n}.node" 2>/dev/null || echo "")
    [[ -z "$want" || "$wm" != "$want" ]] && continue
    (( g < low )) && continue
    [[ -z "$node" || -n "${shut[$node]:-}" ]] && continue
    nodes[$node]=1
  done
  local tally=${#nodes[@]}
  rm -f "$sv/state"/mesh.*.flag
  name=""
  for f in "$sx"/pools.d/*.conf; do
    while IFS= read -r row || [[ -n "${row:-}" ]]; do
      if [[ "$row" =~ ^\[pool\ \"([a-z-]+)\"\]$ ]]; then
        name="${BASH_REMATCH[1]}"
      elif [[ "$row" =~ ^size\ =\ ([0-9]+)$ && -n "${name:-}" ]]; then
        size="${BASH_REMATCH[1]}"
        if (( tally < size )); then
          printf '1\n' >"$sv/state/mesh.${name}.flag"
        else
          printf '0\n' >"$sv/state/mesh.${name}.flag"
        fi
      fi
    done <"$f"
  done
}
fern_h
EOS

# --- Stage 5: canonical emit ---------------------------------------------------
cat >/app/deck/tarn_e.sh <<'EOS'
#!/bin/bash
set -euo pipefail
tarn_e() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local out="${SD_REPORT:-/output/crush-seat.json}"
  local tmp="${out}.tmp"
  local low aim plane rg rmode live agree=1 ok
  local f n wm want g node up inn wv sep row name size pg flag
  low=$(tr -d '[:space:]' <"$sv/gen.low")
  aim=$(tr -d '[:space:]' <"$sv/gen.aim")
  live=$(tr -d '[:space:]' <"$sv/state/gen.live" 2>/dev/null || echo "")
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/prefer.toml" | head -n1)
  rg=""
  rmode=""
  if [[ -f "$sv/state/apply.ok" ]]; then
    rg=$(sed -n 's/^gen=\([0-9]*\)$/\1/p' "$sv/state/apply.ok" | head -n1)
    rmode=$(sed -n 's/^mode=\(.*\)$/\1/p' "$sv/state/apply.ok" | head -n1)
  fi
  {
    printf '{\n'
    printf '  "schema_tag": "crush-seat-v1",\n'
    printf '  "osds": [\n'
    sep=""
    for f in $(ls "$sx"/reweight.d/osd.*.conf | sort -t. -k2 -n); do
      n=${f##*/osd.}
      n=${n%.conf}
      wm=$(sed -n 's/^reweight_milli = \([0-9]*\)$/\1/p' "$f" | head -n1)
      want=$(cat "$sv/state/spine.${n}.wm" 2>/dev/null || echo "")
      g=$(cat "$sv/state/spine.${n}.gen" 2>/dev/null || echo 0)
      node=$(cat "$sv/state/spine.${n}.node" 2>/dev/null || echo "unknown")
      up=false
      if [[ -n "$want" && "$wm" == "$want" ]] && (( g >= low )); then
        up=true
      fi
      if [[ -z "$want" || "$wm" != "$want" ]]; then
        agree=0
      fi
      inn=false
      if [[ "$up" == true && ! -f "$sv/state/knot.${n}.flag" ]]; then
        inn=true
      fi
      wv=$(awk -v m="$wm" 'BEGIN{printf "%g", m/1000}')
      printf '%s' "$sep"
      printf '    {"id": %s, "host": "%s", "weight": %s, "in": %s, "up": %s, "generation": %s}' \
        "$n" "$node" "$wv" "$inn" "$up" "$g"
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
        elif [[ "$row" =~ ^size\ =\ ([0-9]+)$ ]]; then
          size="${BASH_REMATCH[1]}"
        elif [[ "$row" =~ ^pg_num\ =\ ([0-9]+)$ ]]; then
          pg="${BASH_REMATCH[1]}"
        elif [[ "$row" =~ ^state\ = && -n "${name:-}" && -n "${size:-}" && -n "${pg:-}" ]]; then
          flag=false
          if [[ "$(cat "$sv/state/mesh.${name}.flag" 2>/dev/null || echo 0)" == "1" ]]; then
            flag=true
          fi
          printf '%s' "$sep"
          printf '    {"name": "%s", "size": %s, "pg_num": %s, "degraded": %s}' \
            "$name" "$size" "$pg" "$flag"
          sep=$',\n'
          name=""
        fi
      done <"$f"
    done
    printf '\n  ],\n'
    ok=false
    if [[ "$agree" -eq 1 && "$plane" == "durable" && "$rg" == "$aim" \
      && "$rmode" == "seal" && "$live" == "$aim" ]]; then
      ok=true
    fi
    printf '  "seat_ok": %s\n' "$ok"
    printf '}\n'
  } >"$tmp"
  mv "$tmp" "$out"
}
tarn_e
EOS

chmod 755 /app/ops/kelp_v.sh /app/ops/gorse_t.sh /app/lane/moss_q.sh \
  /app/mast/fern_h.sh /app/deck/tarn_e.sh

# --- Select the durable plane -------------------------------------------------
sed -i 's/^plane *= *"surface"/plane = "durable"/' "$SV/prefer.toml"

# --- Converge and verify --------------------------------------------------------
bash /app/ops/run_crush_seat.sh
cp /output/crush-seat.json /tmp/pass1.json
bash /app/ops/run_crush_seat.sh

if ! cmp -s /tmp/pass1.json /output/crush-seat.json; then
  echo "oracle: passes differ" >&2
  exit 1
fi
if ! grep -q '"seat_ok": true' /output/crush-seat.json; then
  echo "oracle: desk did not settle" >&2
  exit 1
fi
if ! grep -q '^gen=' "$SV/state/apply.ok"; then
  echo "oracle: receipt missing" >&2
  exit 1
fi
rm -f /tmp/pass1.json
echo "oracle: desk seated"
