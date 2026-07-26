#!/bin/bash
set -euo pipefail

TOKEN=/data/token
SEED=/data/fixtures/token-seed
mkdir -p "$TOKEN" "$SEED" /output

cat > "$TOKEN/inventory.txt" <<'EOF'
# id role epoch
11 live 5
17 live 7
23 archive 3
29 staging 1
31 live 9
EOF

cat > "$TOKEN/labels.txt" <<'EOF'
# required object labels
signing-leaf
wrap-anchor
EOF

cat > "$TOKEN/provider.txt" <<'EOF'
bound=23
EOF

cat > "$TOKEN/provider.override" <<'EOF'
bound=31
mode=manual
EOF

cat > "$TOKEN/provider.fallback" <<'EOF'
bound=11
mode=auto
EOF

cat > "$TOKEN/objects.txt" <<'EOF'
# label slot_id handle
signing-leaf 11 1001
wrap-anchor 11 1002
signing-leaf 17 2001
wrap-anchor 17 2002
signing-leaf 23 3001
wrap-anchor 23 3002
signing-leaf 29 4001
signing-leaf 31 5001
wrap-anchor 31 5002
EOF

cat > "$TOKEN/sessions.txt" <<'EOF'
# slot pin_alive ttl
11 1 86400
17 0 86400
23 1 86400
29 0 1200
31 0 86400
EOF

cat > "$TOKEN/restore.journal" <<'EOF'
# ledger-blob
01:09
02:a7c3
EOF

cp -a "$TOKEN/inventory.txt" "$SEED/inventory.txt"
cp -a "$TOKEN/labels.txt" "$SEED/labels.txt"
cp -a "$TOKEN/restore.journal" "$SEED/restore.journal"
echo "seed-ok" > "$SEED/marker.txt"

echo "fixtures ready under $TOKEN"
