#!/usr/bin/env bash
set -euo pipefail

cd /app
cat > src/ledger/ledger_row.c <<'ORACLE_EOF'
#include "ledger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int blob_open(uint32_t gen_id) {
    char path[256];
    snprintf(path, sizeof(path), "/app/data/archive_cycle_%u.blob", gen_id);
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        return 0;
    }
    fclose(fp);
    return 1;
}

static uint32_t pick_primary(const ledger_ctx_t *ctx) {
    if (ctx->merge_target != 0 && blob_open(ctx->merge_target)) {
        return ctx->merge_target;
    }
    if (ctx->fallback_id != 0 && blob_open(ctx->fallback_id)) {
        return ctx->fallback_id;
    }
    return 0;
}

int ledger_row_bind(const ledger_ctx_t *ctx, uint32_t *out_gen) {
    if (!ctx || !out_gen) {
        return -1;
    }
    uint32_t picked = pick_primary(ctx);
    if (picked == 0) {
        return -1;
    }
    *out_gen = picked;
    return 0;
}
ORACLE_EOF

cat > src/forge/forge_stage.c <<'ORACLE_EOF'
#include "forge.h"

int forge_stage_mask(void) {
    return 1 | 2 | 4;
}

size_t forge_stage_order(int *out, size_t cap) {
    static const int seq[] = {1, 2, 4};
    size_t n = sizeof(seq) / sizeof(seq[0]);
    for (size_t i = 0; i < n && i < cap; i++) {
        out[i] = seq[i];
    }
    return n;
}
ORACLE_EOF

cat > src/mesh/mesh_adj.c <<'ORACLE_EOF'
#include "mesh.h"

int mesh_adj_refresh(mesh_ctx_t *m, uint32_t gen_id) {
    if (!m) {
        return -1;
    }
    if (gen_id == 0) {
        return -1;
    }
    m->link_gen = gen_id;
    m->links_ready = 1;
    if (!m->layout_ready) {
        mesh_reconcile_layout(m, gen_id);
    }
    return 0;
}
ORACLE_EOF

cat > src/mesh/block_tree.c <<'ORACLE_EOF'
#include "mesh.h"

int mesh_reconcile_layout(mesh_ctx_t *m, uint32_t gen_id) {
    if (!m) {
        return -1;
    }
    (void)gen_id;
    m->layout_ready = 1;
    return 0;
}
ORACLE_EOF

make clean
make

/app/scripts/run_restart.sh

test -f /output/restart-summary.json
test -f /output/fields/alpha/t0.bin
test -f /output/fields/beta/t0.bin
test -f /output/fields/gamma/t1.bin

python3 - <<'PY'
import json
import re
from pathlib import Path

hdr = Path("/app/include/forge.h").read_text()
face_eps = float(re.search(r"#define\s+RESTART_FACE_CAP\s+([0-9.]+)f", hdr).group(1))
mass_eps = float(re.search(r"#define\s+RESTART_DRIFT_CAP\s+([0-9.]+)f", hdr).group(1))
summary = json.loads(Path("/output/restart-summary.json").read_text())
for item in summary["scenarios"]:
    assert item["face_l2"] < face_eps
assert summary["mass_drift"] <= mass_eps
PY
