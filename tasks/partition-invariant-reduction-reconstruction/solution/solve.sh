#!/bin/bash
set -euo pipefail

cat > /app/ws/m3/src/scalar.rs <<'EOF'
pub fn wire_f64_bits(v: f64) -> String {
    let bytes = v.to_be_bytes();
    let mut out = String::with_capacity(16);
    for b in bytes {
        out.push_str(&format!("{b:02x}"));
    }
    out
}
EOF

cat > /app/ws/m7/src/load.rs <<'EOF'
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Checkpoint {
    pub length: usize,
    pub a: Vec<f64>,
    pub b: Vec<f64>,
    pub w: Vec<f64>,
}

pub fn read_checkpoint(path: &std::path::Path) -> std::io::Result<Checkpoint> {
    let raw = std::fs::read_to_string(path)?;
    let ck: Checkpoint = serde_json::from_str(&raw)?;
    if ck.a.len() != ck.length || ck.b.len() != ck.length || ck.w.len() != ck.length {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "checkpoint lane length mismatch",
        ));
    }
    let _ = path;
    Ok(ck)
}
EOF

cat > /app/ws/m7/src/weights.rs <<'EOF'
pub fn blend(a: f64, w: f64) -> f64 {
    let mut acc = a;
    acc *= w;
    acc
}
EOF

cat > /app/ws/m7/src/edge.rs <<'EOF'
use m3::types::Segment;

#[derive(Clone, Copy, Debug)]
pub struct Cell {
    pub idx: usize,
    pub a: f64,
    pub b: f64,
    pub w: f64,
}

fn push_owned(out: &mut Vec<Cell>, ck: &crate::load::Checkpoint, idx: usize) {
    out.push(Cell {
        idx,
        a: ck.a[idx],
        b: ck.b[idx],
        w: ck.w[idx],
    });
}

pub fn gather_lane(seg: &Segment, ck: &crate::load::Checkpoint, _overlap: u32) -> Vec<Cell> {
    let mut out = Vec::with_capacity(seg.hi.saturating_sub(seg.lo));
    let lo = seg.lo.min(ck.length);
    let hi = seg.hi.min(ck.length);
    let mut i = lo;
    while i < hi {
        push_owned(&mut out, ck, i);
        i += 1;
    }
    out
}
EOF

cat > /app/ws/m9/src/stage.rs <<'EOF'
pub fn merge_lane(a: f64, b: f64, _lane_tag: u32) -> f64 {
    let mut s = a;
    s += b;
    s
}

pub fn fold_vec(vals: &[f64], _width: u32) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut layer = vals.to_vec();
    while layer.len() > 1 {
        let mut nxt = Vec::with_capacity(layer.len().div_ceil(2));
        let mut i = 0usize;
        while i < layer.len() {
            if i + 1 < layer.len() {
                nxt.push(merge_lane(layer[i], layer[i + 1], 0));
                i += 2;
            } else {
                nxt.push(layer[i]);
                i += 1;
            }
        }
        layer = nxt;
    }
    layer[0]
}
EOF

cat > /app/ws/m9/src/session.rs <<'EOF'
use m3::scalar::wire_f64_bits;
use m3::types::{LayoutSpec, MetricBundle};
use m7::edge::Cell;
use m7::load::Checkpoint;

fn reduce_mode(cells: &[Cell], mode: u8) -> f64 {
    let mut ordered: Vec<Cell> = Vec::with_capacity(cells.len());
    ordered.extend_from_slice(cells);
    ordered.sort_by_key(|c| c.idx);
    let mut write = 0usize;
    for read in 0..ordered.len() {
        if write == 0 || ordered[read].idx != ordered[write - 1].idx {
            ordered[write] = ordered[read];
            write += 1;
        }
    }
    ordered.truncate(write);

    let mut total = 0.0f64;
    for cell in &ordered {
        let v = match mode {
            0 => m7::weights::blend(cell.a, cell.w),
            1 => cell.a * cell.b,
            _ => cell.a * cell.a,
        };
        total = total + v;
    }
    total
}

pub fn run_session(layout: &LayoutSpec, ck: &Checkpoint) -> MetricBundle {
    let mut all_cells: Vec<Cell> = Vec::new();
    for seg in &layout.segments {
        all_cells.extend(m7::edge::gather_lane(seg, ck, layout.overlap));
    }
    MetricBundle {
        sum_w_bits: wire_f64_bits(reduce_mode(&all_cells, 0)),
        dot_ab_bits: wire_f64_bits(reduce_mode(&all_cells, 1)),
        l2_sq_bits: wire_f64_bits(reduce_mode(&all_cells, 2)),
    }
}
EOF

python3 - <<'PY'
from pathlib import Path
topo = Path('/app/ws/m9/src/topology.rs')
text = topo.read_text()
text = text.replace('    if ranks > 2 {\n        segments.reverse();\n    }\n', '')
topo.write_text(text)
disp = Path('/app/ws/m5/src/dispatch.rs')
d = disp.read_text()
d = d.replace(
    'let owner = (seg.rank + 1).min(last_rank);\n                layout_owners.insert(seg.hi.to_string(), owner);',
    'layout_owners.insert(seg.hi.to_string(), seg.rank);',
)
disp.write_text(d)
PY

cd /app/ws
cargo build --release --locked --offline
/app/ws/target/release/rx-run all-layouts --out-dir /output
