#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin cluster digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"
CLUSTER="$DATA/cluster"

mkdir -p /etc/corosync/nodes /etc/pacemaker/cib.d /etc/pacemaker/floors \
  /var/lib/pacemaker/floors /var/lib/pacemaker/resources /var/lib/pacemaker/state \
  /var/lib/cluster/ops/abort.d /var/lib/cluster/ops/state \
  /var/run/cluster /var/log/cluster /output

cp -a "$CLUSTER/nodes.roster" /var/lib/pacemaker/nodes.roster
cp -a "$CLUSTER/resources.roster" /var/lib/pacemaker/resources.roster
cp -a "$CLUSTER/resources/." /var/lib/pacemaker/resources/
cp -a "$SEED/cib.d/." /etc/pacemaker/cib.d/
cp -a "$SEED/abort.d/." /var/lib/cluster/ops/abort.d/
cp -a "$SEED/prefer_journal.jsonl" /var/lib/cluster/ops/prefer_journal.jsonl
cp -a "$SEED/fence_journal.jsonl" /var/lib/cluster/ops/fence_journal.jsonl
cp -a "$SEED/corosync_nodes/." /etc/corosync/nodes/

printf '7\n' >/var/lib/cluster/ops/state/gen.target
printf '3\n' >/var/lib/cluster/ops/state/gen.live
rm -f /var/lib/cluster/ops/state/cutover.ok

# Durable floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/pacemaker/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live decoy floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/pacemaker/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Stale tip generations (pre-cutover)
for n in node_a node_b node_c; do
  printf '1\n' >"/var/lib/pacemaker/state/tip_${n}.gen"
  printf '0\n' >"/var/lib/pacemaker/state/online_${n}"
done

# Packaging digest for immutable fixtures
(
  cd "$CLUSTER"
  find . -type f | sort | xargs sha256sum
) >"$ROOT/packaging/cluster.sha256"

cp -a "$ROOT/packaging/cluster.sha256" /app/packaging/cluster.sha256 2>/dev/null || true
