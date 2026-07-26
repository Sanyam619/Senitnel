#!/usr/bin/env bash
set -euo pipefail

UNIFIED="/data/lab/cgroup/unified"
LEGACY="/data/lab/cgroup/v1"
ANCHOR="/data/fixtures/cgroup-seed"
SLICE="app.slice"

write_leaf() {
  local dir="$1" leaf="$2" body="$3"
  mkdir -p "$dir"
  printf '%s\n' "$body" > "${dir}/${leaf}"
}

mkdir -p /output

write_leaf "$UNIFIED" "cgroup.controllers" "cpu io memory pids"
write_leaf "$UNIFIED" "cgroup.subtree_control" "cpu pids"
write_leaf "$UNIFIED/$SLICE" "cgroup.controllers" "cpu io memory pids"
write_leaf "$UNIFIED/$SLICE" "cgroup.subtree_control" ""

for unit in app-batch.scope app-worker.scope; do
  write_leaf "$UNIFIED/$SLICE/$unit" "cgroup.controllers" "cpu io memory pids"
done

for ctrl in cpu io memory; do
  write_leaf "$LEGACY/$ctrl/app-api.scope" "cgroup.controllers" "$ctrl"
done

rm -rf "$ANCHOR"
mkdir -p "$ANCHOR"
tar -C /data/lab/cgroup -cf - . | tar -C "$ANCHOR" -xf -
printf 'anchor=v1\n' > "$ANCHOR/manifest.txt"

(
  cd "$ANCHOR"
  find . -type f ! -name 'checksums.sha256' -print | sort | while read -r rel; do
    rel="${rel#./}"
    sha256sum "$rel"
  done
) > "$ANCHOR/checksums.sha256"

chmod -R a+rX /data/lab/cgroup "$ANCHOR" 2>/dev/null || true
