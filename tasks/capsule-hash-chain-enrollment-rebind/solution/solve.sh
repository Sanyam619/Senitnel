#!/bin/bash
set -euo pipefail

# Rewrite the three decision bodies, rebuild every tool, and run enrollment.

cat > /app/frame/fold_q.c <<'EOF'
#include <string.h>

#include "frame.h"
#include "fold_q.h"

int fold_q(const struct row_q *a, struct slot_q *b)
{
    int leaf_ok = (a->leaf != NULL && a->leaf[0] != '\0');
    int parent_ok = (a->parent != NULL && a->parent[0] != '\0');
    int anchor_ok = (a->anchor != NULL && a->anchor[0] != '\0');

    b->sig_ok = (a->sig != NULL && a->sig[0] != '\0');
    b->gen = a->gen;

    if (!leaf_ok || !parent_ok || !anchor_ok) {
        b->tip_ok = 0;
        return 0;
    }

    if (strcmp(a->parent, a->anchor) != 0) {
        b->tip_ok = 0;
        return 0;
    }

    b->tip_ok = 1;
    return 0;
}
EOF

cat > /app/policy/src/gate_r.rs <<'EOF'
use crate::{RowR, SlotR};

pub fn gate_r(a: &RowR, b: &mut SlotR) -> i32 {
    let mut marked = false;
    for m in &a.marks {
        if m.as_str() == a.id.as_str() {
            marked = true;
            break;
        }
    }

    if !marked {
        b.code = 0;
        return b.code;
    }

    if a.claim < a.lo {
        b.code = 1;
        return b.code;
    }
    if a.claim > a.hi {
        b.code = 1;
        return b.code;
    }

    b.code = 2;
    b.code
}
EOF

cat > /app/enroll/internal/slot_w.go <<'EOF'
package internal

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// RowW carries the roots directory and the value the root lines up with.
type RowW struct {
	Dir   string
	Bound int64
}

// SlotW carries the resolved root generation and whether it lines up.
type SlotW struct {
	Anchor int64
	Ok     bool
}

func slot_w(a RowW, b *SlotW) error {
	path := filepath.Join(a.Dir, "disk.bundle")
	raw, err := os.ReadFile(path)
	if err != nil {
		b.Anchor = -1
		b.Ok = false
		return err
	}

	rootTok, genVal := parseBundle(raw)
	if rootTok == "" || genVal < 0 {
		b.Anchor = -1
		b.Ok = false
		return nil
	}

	b.Anchor = genVal
	b.Ok = genVal == a.Bound
	return nil
}

func parseBundle(raw []byte) (string, int64) {
	rootTok := ""
	genVal := int64(-1)
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "root=") {
			rootTok = strings.TrimSpace(line[len("root="):])
			continue
		}
		if strings.HasPrefix(line, "gen=") {
			if n, err := strconv.ParseInt(strings.TrimSpace(line[len("gen="):]), 10, 64); err == nil {
				genVal = n
			}
		}
	}
	return rootTok, genVal
}
EOF

cd /app
make
/app/scripts/run-enroll.sh
