#!/usr/bin/env bash
set -euo pipefail
unit="$1"
src="/data/stack/units/$unit"
drop="/data/stack/overrides/${unit}.d"
out="/data/stack/runtime/$unit"
mkdir -p "$out"
cp "$src" "$out/merged.ini"
if [[ -d "$drop" ]]; then
  mapfile -t files < <(find "$drop" -maxdepth 1 -type f -name '*.conf' | sort)
  for frag in "${files[@]}"; do
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
      key="${line%%=*}"
      val="${line#*=}"
      sed -i "/^${key}=/d" "$out/merged.ini"
      printf '%s=%s\n' "$key" "$val" >> "$out/merged.ini"
    done < "$frag"
  done
fi
