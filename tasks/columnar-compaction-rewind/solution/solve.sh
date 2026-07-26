#!/bin/bash
set -euo pipefail
export LC_ALL=C

DATA=/app/data
OUT=/output
mkdir -p "$OUT/view"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------- manifests
jq -c '.' "$DATA"/manifests/tier_a.jsonl "$DATA"/manifests/tier_b.jsonl \
  "$DATA"/manifests/tier_c.jsonl > "$WORK/entries.jsonl"

stripe_file() {
  local ns=$1 sid=$2
  if [ "$sid" -eq 99 ]; then
    echo "$DATA/columns/${ns}_merged.col"
  else
    printf '%s/columns/%s_%03d.col\n' "$DATA" "$ns" "$sid"
  fi
}

resolved_entry() { # ns gen -> compact JSON of newest entry with gen <= G (or empty)
  jq -c -s --arg ns "$1" --argjson g "$2" \
    'map(select(.ns == $ns and .gen <= $g)) | max_by(.gen) // empty' \
    "$WORK/entries.jsonl"
}

entry_verifies() { # compact entry JSON -> 0 if every listed stripe file matches its sha
  local entry=$1 sid path want got
  while read -r sid; do
    path=$(stripe_file "$(jq -r '.ns' <<<"$entry")" "$sid")
    [ -f "$path" ] || return 1
    want=$(jq -r --arg s "$sid" '.sha256[$s]' <<<"$entry")
    got=$(sha256sum "$path" | cut -d' ' -f1)
    [ "$want" = "$got" ] || return 1
  done < <(jq -r '.stripes[]' <<<"$entry")
  return 0
}

NAMESPACES=$(jq -r '.ns' "$WORK/entries.jsonl" | sort -u)
GENS=$(jq -r '.gen' "$WORK/entries.jsonl" | sort -nu)

RESTORED=""
for g in $GENS; do
  ok=1
  for ns in $NAMESPACES; do
    entry=$(resolved_entry "$ns" "$g")
    if [ -z "$entry" ] || ! entry_verifies "$entry"; then
      ok=0
      break
    fi
  done
  [ "$ok" -eq 1 ] && RESTORED=$g
done
[ -n "$RESTORED" ] || { echo "no consistent generation found" >&2; exit 1; }

# ---------------------------------------------------------------- WAL decode
cat > "$WORK/wal.awk" <<'AWK'
function lehex(s,   i, out) {
  out = ""
  for (i = length(s) - 1; i >= 1; i -= 2) out = out substr(s, i, 2)
  return strtonum("0x" out)
}
function hexstr(s,   i, out) {
  out = ""
  for (i = 1; i < length(s); i += 2) out = out sprintf("%c", strtonum("0x" substr(s, i, 2)))
  return out
}
{
  hex = $0
  n = length(hex)
  pos = 11                     # skip 4-byte magic + version byte
  while (pos + 17 <= n) {      # 9 bytes (seq + op) fully present
    seq = lehex(substr(hex, pos, 16)); pos += 16
    op = strtonum("0x" substr(hex, pos, 2)); pos += 2
    if (op == 2) { printf "%d\tchk\t\t\t\t\n", seq; continue }
    if (pos + 1 > n) break
    nslen = strtonum("0x" substr(hex, pos, 2)); pos += 2
    if (pos + nslen * 2 + 3 > n) break
    ns = hexstr(substr(hex, pos, nslen * 2)); pos += nslen * 2
    klen = lehex(substr(hex, pos, 4)); pos += 4
    if (pos + klen * 2 - 1 > n) break
    key = hexstr(substr(hex, pos, klen * 2)); pos += klen * 2
    if (op == 0) {
      if (pos + 31 > n) break
      val = lehex(substr(hex, pos, 16)); pos += 16
      ts = lehex(substr(hex, pos, 16)); pos += 16
      printf "%d\tput\t%s\t%s\t%d\t%d\n", seq, ns, key, val, ts
    } else {
      printf "%d\tdel\t%s\t%s\t\t\n", seq, ns, key
    }
  }
}
AWK

: > "$WORK/ops_raw.tsv"
for seg in "$DATA"/wal/seg_*.bin; do
  od -An -v -tx1 "$seg" | tr -d ' \n' | gawk -f "$WORK/wal.awk" >> "$WORK/ops_raw.tsv"
done

# one operation per sequence number (re-appended ranges are byte-identical)
sort -t "$(printf '\t')" -k1,1n -u "$WORK/ops_raw.tsv" > "$WORK/ops.tsv"

CHECKPOINT=$(gawk -F'\t' '$2 == "chk" && $1 > m { m = $1 } END { print m + 0 }' "$WORK/ops.tsv")
DURABLE=$(gawk -F'\t' -v c="$CHECKPOINT" '$2 != "chk" && $1 <= c' "$WORK/ops.tsv" | wc -l | tr -d ' ')
REWOUND=$(gawk -F'\t' -v c="$CHECKPOINT" '$2 != "chk" && $1 > c' "$WORK/ops.tsv" | wc -l | tr -d ' ')

# ---------------------------------------------------------------- per-namespace views
cat > "$WORK/apply.awk" <<'AWK'
BEGIN { FS = "\t"; OFS = "\t" }
FNR == NR { state[$1] = $2 OFS $3; held[$1] = 1; next }
$2 == "put" { state[$4] = $5 OFS $6; held[$4] = 1 }
$2 == "del" { delete state[$4] }
END {
  removed = 0
  for (k in held) if (!(k in state)) removed++
  for (k in state) print k, state[k]
  print removed > ENVIRON["REMOVED_OUT"]
}
AWK

NS_JSON="{}"
for ns in $NAMESPACES; do
  entry=$(resolved_entry "$ns" "$RESTORED")
  visible=$(jq -r '.stripes | length' <<<"$entry")

  # base records in stripe-list order: later stripes supersede earlier ones
  : > "$WORK/base_$ns.tsv"
  while read -r sid; do
    jq -r '.records[] | [.k, .v, .t] | @tsv' "$(stripe_file "$ns" "$sid")" \
      >> "$WORK/base_$ns.tsv"
  done < <(jq -r '.stripes[]' <<<"$entry")

  gawk -F'\t' -v c="$CHECKPOINT" -v ns="$ns" \
    '$2 != "chk" && $1 <= c && $3 == ns' "$WORK/ops.tsv" \
    | sort -t "$(printf '\t')" -k1,1n > "$WORK/durable_$ns.tsv"

  REMOVED_OUT="$WORK/removed_$ns" \
    gawk -f "$WORK/apply.awk" "$WORK/base_$ns.tsv" "$WORK/durable_$ns.tsv" \
    | sort -t "$(printf '\t')" -k1,1 > "$OUT/view/$ns.tsv"

  removed=$(cat "$WORK/removed_$ns")
  live=$(wc -l < "$OUT/view/$ns.tsv" | tr -d ' ')
  total=$(gawk -F'\t' '{ s += $2 } END { print s + 0 }' "$OUT/view/$ns.tsv")
  digest=$(sha256sum "$OUT/view/$ns.tsv" | cut -d' ' -f1)

  NS_JSON=$(jq -c --arg ns "$ns" --argjson vs "$visible" --argjson lk "$live" \
    --argjson rk "$removed" --argjson vt "$total" --arg dg "$digest" \
    '. + {($ns): {visible_stripes: $vs, live_keys: $lk, removed_keys: $rk,
                  value_total: $vt, view_digest: $dg}}' <<<"$NS_JSON")
done

jq -n --argjson rg "$RESTORED" --argjson cs "$CHECKPOINT" \
  --argjson d "$DURABLE" --argjson r "$REWOUND" --argjson ns "$NS_JSON" \
  '{restored_generation: $rg, checkpoint_seq: $cs,
    wal: {durable_ops: $d, rewound_ops: $r}, namespaces: $ns}' \
  > "$OUT/rewind-report.json"

jq -e '.restored_generation > 0' "$OUT/rewind-report.json" > /dev/null
