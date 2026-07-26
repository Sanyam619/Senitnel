#!/usr/bin/env bash
set -euo pipefail

cd /opt/distro

module_cp() {
  local parts=()
  for dir in mod-m7/target/classes mod-p3/target/classes mod-k9/target/classes app-module/target/classes; do
    if [[ -d "$dir" ]]; then
      parts+=("$dir")
    fi
  done
  local IFS=:
  echo "${parts[*]}"
}

CP="$(module_cp)"

javac -cp "$CP" -d mod-p3/target/classes \
  mod-p3/src/main/java/com/distro/engine/p3/PhaseK.java

javac -cp "$CP" -d mod-m7/target/classes \
  mod-m7/src/main/java/com/distro/ingest/m7/ScanC.java

javac -cp "$CP" -d mod-k9/target/classes \
  mod-k9/src/main/java/com/distro/core/k9/Step2.java

rm -rf /tmp/jar-build
mkdir -p /tmp/jar-build
for dir in mod-m7/target/classes mod-p3/target/classes mod-k9/target/classes app-module/target/classes; do
  if [[ -d "$dir" ]]; then
    cp -r "$dir/." /tmp/jar-build/
  fi
done

jar cfm /opt/distro/target/cycle-batch-1.0.0.jar /opt/distro/config/jar-manifest.mf -C /tmp/jar-build .
