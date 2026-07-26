#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/traefik/dynamic /etc/traefik/floors \
  /var/lib/traefik/ops/abort.d /var/lib/traefik/ops/floors \
  /var/lib/traefik/ops/seeds /var/lib/traefik/ops/state \
  /var/run/traefik /var/log/traefik /output

cp -a "$SEED/traefik.yml" /etc/traefik/traefik.yml
cp -a "$SEED/dynamic/." /etc/traefik/dynamic/
cp -a "$SEED/abort.d/." /var/lib/traefik/ops/abort.d/
cp -a "$SEED/seeds/." /var/lib/traefik/ops/seeds/
cp -a "$SEED/journal.jsonl" /var/lib/traefik/ops/journal.jsonl
cp -a "$SEED/retired_tips.jsonl" /var/lib/traefik/ops/retired_tips.jsonl
cp -a "$SEED/prefer.toml" /var/lib/traefik/ops/prefer.toml
cp -a "$SEED/tip_bind.accept" /var/lib/traefik/ops/tip_bind.accept
cp -a "$SEED/mw_prefer.toml" /var/lib/traefik/ops/mw_prefer.toml
cp -a "$DATA/roster.list" /etc/traefik/roster.list
printf '%s\n' compress authstrip ratelimit headers >/etc/traefik/mw.list

printf '7\n' >/var/lib/traefik/ops/state/gen.target
printf '3\n' >/var/lib/traefik/ops/state/gen.live
rm -f /var/lib/traefik/ops/state/cutover.ok

while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/var/lib/traefik/ops/floors/${k}.floor"
done <"$SEED/floors.toml"

while IFS='=' read -r k v || [[ -n "${k:-}" ]]; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  k=$(echo "$k" | tr -d '[:space:]')
  v=$(echo "$v" | tr -d '[:space:]')
  [[ -z "$k" ]] && continue
  printf '%s\n' "$v" >"/etc/traefik/floors/${k}.floor"
done <"$SEED/live_floors.toml"

for n in alpha beta gamma delta epsilon; do
  printf '1\n' >"/var/lib/traefik/ops/state/tip_${n}.gen"
done

cp -f /var/lib/traefik/ops/abort.d/90-abort.yml /etc/traefik/dynamic/90-local.yml

(
  cd "$DATA/traefik"
  sha256sum ./*.toml | sort
) >"$ROOT/packaging/traefik.sha256"
