#!/bin/bash
set -euo pipefail

# Rewrite the three decision bodies, rebuild native+Java, run pack emit.

cat > /app/native/knit_xv.c <<'EOF'
#include "knit_xv.h"

int knit_xv(const struct row_x *a, struct slot_x *b)
{
    int pr;
    int mt;
    int wr;
    int wm;
    int pack_match;
    int mode_match;

    if (a == 0) {
        b->pack_ok = 0;
        b->mode_tag = 0;
        return -1;
    }

    pr = a->pack_rank;
    mt = a->mode_tag;
    wr = a->want_rank;
    wm = a->want_mode;

    if (wr < 0 || wm < 0) {
        b->pack_ok = 0;
        b->mode_tag = mt;
        return 0;
    }

    if (pr < 0 || mt < 0) {
        b->pack_ok = 0;
        b->mode_tag = 0;
        return 0;
    }

    pack_match = (pr == wr) ? 1 : 0;
    mode_match = (mt == wm) ? 1 : 0;

    if (pack_match == 0) {
        b->pack_ok = 0;
        b->mode_tag = mt;
        return 0;
    }

    if (mode_match == 0) {
        b->pack_ok = 0;
        b->mode_tag = mt;
        return 0;
    }

    if (pr != wr || mt != wm) {
        b->pack_ok = 0;
        b->mode_tag = mt;
        return 0;
    }

    b->mode_tag = mt;
    b->pack_ok = 1;
    return 0;
}
EOF

cat > /app/nest/OpB.java <<'EOF'
package nest;

public final class OpB {
    private OpB() {}

    public static int op_b(RowY a, SlotY b) {
        if (a == null) {
            b.code = 0;
            return b.code;
        }

        int claim = a.claim;
        int lo = a.lo;
        int hi = a.hi;
        boolean marked = a.marked;

        if (!marked) {
            b.code = 0;
            return b.code;
        }

        if (lo > hi) {
            b.code = 1;
            return b.code;
        }

        if (claim < 0) {
            b.code = 1;
            return b.code;
        }

        if (claim >= lo && claim <= hi) {
            b.code = 2;
            return b.code;
        }

        if (claim < lo) {
            b.code = 1;
            return b.code;
        }

        b.code = 1;
        return b.code;
    }
}
EOF

cat > /app/forge/OpC.java <<'EOF'
package forge;

public final class OpC {
    private OpC() {}

    public static int op_c(RowZ a, SlotZ b) {
        if (a == null) {
            b.genOk = 0;
            return b.genOk;
        }

        int claim = a.claimGen;
        int durable = a.durableGen;
        int live = a.liveGen;

        if (durable <= 0) {
            b.genOk = 0;
            return b.genOk;
        }

        if (claim <= 0) {
            b.genOk = 0;
            return b.genOk;
        }

        if (live == claim && durable != claim) {
            b.genOk = 0;
            return b.genOk;
        }

        if (live > 0 && live != durable && claim == live) {
            b.genOk = 0;
            return b.genOk;
        }

        if (claim == durable) {
            b.genOk = 1;
            return b.genOk;
        }

        b.genOk = 0;
        return b.genOk;
    }
}
EOF

cd /app
make install
/app/scripts/run-pack.sh
