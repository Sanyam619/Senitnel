#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p /data/blobs /data/traces /data/rly /data/fixtures/anchor-blobs /opt/rly/keys /output

printf 'release payload alpha v1\n' > /data/blobs/release-a.bin
printf 'release payload beta v1\n' > /data/blobs/release-b.bin
cp /data/blobs/release-a.bin /data/fixtures/anchor-blobs/release-a.bin
cp /data/blobs/release-b.bin /data/fixtures/anchor-blobs/release-b.bin

cat > /data/traces/primary.evt <<'EOF'
{"idx":0,"bank":0,"payload":"CRTM"}
{"idx":1,"bank":0,"payload":"PostCode"}
{"idx":2,"bank":1,"payload":"PlatformConfig"}
{"idx":3,"bank":7,"payload":"OptionRom"}
{"idx":4,"bank":8,"payload":"BootLoader"}
EOF

cat > /data/traces/shadow.evt <<'EOF'
{"idx":0,"bank":0,"payload":"CRTM"}
{"idx":1,"bank":0,"payload":"PostCode"}
{"idx":2,"bank":1,"payload":"PlatformConfig"}
{"idx":3,"bank":7,"payload":"OptionRom"}
{"idx":4,"bank":8,"payload":"BootLoader"}
{"idx":100,"bank":8,"payload":"FwCfg-v2"}
{"idx":101,"bank":7,"payload":"FwPatch-v2"}
EOF

if [ ! -f /opt/rly/keys/quote.pem ]; then
  openssl genrsa -out /opt/rly/keys/quote.pem 2048 2>/dev/null
  openssl rsa -in /opt/rly/keys/quote.pem -pubout -out /opt/rly/keys/quote.pub 2>/dev/null
fi

(
  cd /data/fixtures/anchor-blobs
  sha256sum release-a.bin release-b.bin > checksums.sha256
)

/opt/rly/bin/fwreplay --traces /data/traces --state /data/rly/chip-state.json
/opt/rly/bin/sealmake --out /output/attestation-bundle.json

echo "fixtures ready"
