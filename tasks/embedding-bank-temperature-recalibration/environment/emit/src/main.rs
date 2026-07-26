use std::collections::BTreeMap;
use std::fmt::Write as _;
use std::fs;
use std::io::Write as _;
use std::path::{Path, PathBuf};

use bevel_core::base::{self, Lot};
use bevel_core::gauge;
use bevel_core::lens;
use bevel_core::weave;
use bevel_rank::dial;
use bevel_rank::lace;

const APP_ROOT: &str = "/app";

struct CellOut {
    id: &'static str,
    hits: usize,
    nq: usize,
    nrows: usize,
    r10: f64,
    nmi: f64,
}

struct Board {
    idx: u32,
    tau: f64,
    cells: Vec<CellOut>,
}

fn app_root() -> PathBuf {
    match std::env::var("BEVEL_ROOT") {
        Ok(v) if !v.is_empty() => PathBuf::from(v),
        _ => PathBuf::from(APP_ROOT),
    }
}

fn empty_lot(name: &str) -> Lot {
    Lot {
        name: name.to_string(),
        tags: Vec::new(),
        lw: Vec::new(),
        rows: Vec::new(),
    }
}

fn compute() -> Board {
    let root = app_root().join("data");
    let marks = base::read_marks(&root.join("feature_registry/tip_journal.jsonl"));
    let bind = lace::lace_b(&marks, &root);
    let idx = bind.idx;
    let tau = bind.tau;
    let retired = bevel_rank::knot::read_retired(&root.join("feature_registry/retired_tips.jsonl"));
    let lots_a = base::read_dir_lots(&root.join("banks/bank_a"), "bank_a");
    let lots_b = base::read_dir_lots(&root.join("banks/bank_b"), "bank_b");
    let mut all = lots_a.clone();
    all.extend(lots_b.iter().cloned());
    let fam_a = base::fold_all(&lots_a, "a");
    let fam_b = base::fold_all(&lots_b, "b");
    let mixed = weave::weave_m(&marks, &all, &retired);
    let (mix_c, mix_d) = if mixed.len() == 2 {
        (mixed[0].clone(), mixed[1].clone())
    } else {
        (empty_lot("c"), empty_lot("d"))
    };
    let load = |n: &str| base::read_blob(&root.join("checkpoints").join(n));
    let plan: Vec<(&'static str, Vec<u8>, &Lot)> = vec![
        ("cold_a", load("cold_a.ckpt"), &fam_a),
        ("resume_a", load("resume_a.ckpt"), &fam_a),
        ("cold_b", load("cold_b.ckpt"), &fam_b),
        ("resume_b", load("resume_b.ckpt"), &fam_b),
        ("mix_c", load("resume_a.ckpt"), &mix_c),
        ("mix_d", load("resume_b.ckpt"), &mix_d),
    ];
    let mut cells = Vec::new();
    for (id, blob, lot) in plan {
        let qs = lens::lens_unfold(&blob);
        let qt = base::read_tags(&blob);
        let hits = gauge::hits_at(&qs, &qt, lot, tau, 10);
        let nq = qs.len();
        let r10 = if nq > 0 { hits as f64 / nq as f64 } else { 0.0 };
        let nmi = gauge::agree(&qs, &qt, lot, tau);
        cells.push(CellOut {
            id,
            hits,
            nq,
            nrows: lot.rows.len(),
            r10,
            nmi,
        });
    }
    Board { idx, tau, cells }
}

struct Band {
    r_lo: f64,
    r_hi: f64,
    n_lo: f64,
    n_hi: f64,
    t_lo: f64,
    t_hi: f64,
}

fn read_bands(path: &Path) -> BTreeMap<String, Band> {
    let mut out = BTreeMap::new();
    let Ok(text) = fs::read_to_string(path) else {
        return out;
    };
    for line in text.lines() {
        let line = line.trim();
        if !line.starts_with('|') {
            continue;
        }
        let cols: Vec<&str> = line
            .trim_matches('|')
            .split('|')
            .map(|c| c.trim())
            .collect();
        if cols.len() < 7 {
            continue;
        }
        let vals: Vec<Option<f64>> = cols[1..7].iter().map(|c| c.parse::<f64>().ok()).collect();
        if vals.iter().any(|v| v.is_none()) {
            continue;
        }
        let v: Vec<f64> = vals.into_iter().map(|v| v.unwrap_or(0.0)).collect();
        out.insert(
            cols[0].to_string(),
            Band {
                r_lo: v[0],
                r_hi: v[1],
                n_lo: v[2],
                n_hi: v[3],
                t_lo: v[4],
                t_hi: v[5],
            },
        );
    }
    out
}

fn fmt6(v: f64) -> String {
    format!("{v:.6}")
}

fn run_eval(out_path: Option<PathBuf>) {
    let board = compute();
    let bands = read_bands(&app_root().join("docs/embed_bands.md"));
    let mut ok = !board.cells.is_empty();
    for c in &board.cells {
        match bands.get(c.id) {
            Some(b) => {
                let fit = c.r10 >= b.r_lo
                    && c.r10 <= b.r_hi
                    && c.nmi >= b.n_lo
                    && c.nmi <= b.n_hi
                    && board.tau >= b.t_lo
                    && board.tau <= b.t_hi;
                if !fit {
                    ok = false;
                }
            }
            None => {
                ok = false;
            }
        }
    }
    let mut s = String::new();
    s.push_str("{\"schema_tag\":\"embed-eval-v2\",\"scenarios\":[");
    for (i, c) in board.cells.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        let _ = write!(
            s,
            "{{\"id\":\"{}\",\"recall_at_10\":{},\"nmi\":{},\"temperature\":{},\"bank_epoch\":{}}}",
            c.id,
            fmt6(c.r10),
            fmt6(c.nmi),
            fmt6(board.tau),
            board.idx
        );
    }
    s.push_str("],\"bands_ok\":");
    s.push_str(if ok { "true" } else { "false" });
    s.push_str("}\n");
    write_out(out_path, &s);
}

fn run_trace(out_path: Option<PathBuf>) {
    let board = compute();
    let cfg = dial::dial_v(&app_root().join("calib"));
    let mut lines: Vec<String> = Vec::new();
    for c in &board.cells {
        lines.push(format!(
            "{{\"cell\":\"{}\",\"rows\":{},\"q\":{},\"hits\":{},\"x\":{},\"t\":{}}}",
            c.id,
            c.nrows,
            c.nq,
            c.hits,
            board.idx,
            fmt6(board.tau)
        ));
    }
    let mut s = String::new();
    let mut in_flight = 0usize;
    for line in &lines {
        s.push_str(line);
        s.push('\n');
        in_flight += 1;
        if in_flight >= cfg.stride {
            in_flight = 0;
        }
    }
    write_out(out_path, &s);
}

fn write_out(out_path: Option<PathBuf>, body: &str) {
    match out_path {
        Some(p) => {
            if let Some(dir) = p.parent() {
                let _ = fs::create_dir_all(dir);
            }
            fs::write(&p, body).unwrap_or_else(|e| {
                eprintln!("write {}: {e}", p.display());
                std::process::exit(1);
            });
        }
        None => {
            let stdout = std::io::stdout();
            let mut h = stdout.lock();
            let _ = h.write_all(body.as_bytes());
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).cloned().unwrap_or_default();
    let mut out_path: Option<PathBuf> = None;
    let mut i = 2usize;
    while i < args.len() {
        if args[i] == "--out" && i + 1 < args.len() {
            out_path = Some(PathBuf::from(&args[i + 1]));
            i += 2;
        } else {
            i += 1;
        }
    }
    match mode.as_str() {
        "eval" => run_eval(out_path),
        "trace" => run_trace(out_path),
        _ => {
            eprintln!("usage: bevel <eval|trace> [--out <path>]");
            std::process::exit(2);
        }
    }
}
