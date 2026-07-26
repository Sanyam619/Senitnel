#!/bin/bash
set -euo pipefail

cat > /app/ops/prefer.toml <<'EOF'
# Host seating preference — durable authority restored.

[token]
root = "durable"
bind = "authority"
EOF

cat > /app/qx/internal/seat_k.go <<'EOF'
package internal

var SeatMode = "durable"

var SeatAllow = "/data/vault/"
EOF

cat > /app/qx/internal/band_k.go <<'EOF'
package internal

var BandLo int64 = 4

var BandHi int64 = 9
EOF

cat > /app/rz/mat_q.c <<'EOF'
#include <stdint.h>
#include <string.h>

#include "mat_q.h"

static unsigned char rotl8(unsigned char x, unsigned n)
{
    n %= 8u;
    return (unsigned char)((x << n) | (x >> (8u - n)));
}

void mat_q(const unsigned char *seed, size_t n, unsigned epoch,
           unsigned lane, unsigned strand, unsigned char *out)
{
    size_t i;
    unsigned char elo = (unsigned char)(epoch & 0xffu);
    for (i = 0; i < n; i++) {
        unsigned char mix = rotl8(elo, (unsigned)((i % 5) + 1));
        unsigned char stride = (unsigned char)((5u * (unsigned)i + 1u) & 0xffu);
        out[i] = (unsigned char)(seed[i] ^ mix ^ stride ^ (unsigned char)strand ^ (unsigned char)lane);
    }
}
EOF

cat > /app/rz/knit_m.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "knit_m.h"

int knit_m(const unsigned char *payload, size_t n,
           const unsigned char *material, size_t mlen,
           unsigned expect)
{
    unsigned sum = 0;
    size_t i;
    if (mlen == 0) {
        return 0;
    }
    for (i = 0; i < n; i++) {
        sum = (sum + (payload[i] ^ material[i % mlen])) & 0xffu;
    }
    return sum == (expect & 0xffu);
}
EOF

python3 - <<'PY'
import json
from pathlib import Path
journal = Path("/app/data/seating/canon.journal")
out = ["# durable seating recovered from sealed seating journal"]
m = {}
for line in journal.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    row = json.loads(line)
    alias = row["alias"]
    if "canon" in row:
        m[alias] = row["canon"]
    elif "via" in row:
        m[alias] = row["via"]
for k in sorted(m):
    out.append(f"{k}={m[k]}")
Path("/app/data/roots/durable.map").write_text("\n".join(out) + "\n")
PY

cd /app
make
/app/scripts/run-admit.sh
