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
/// Maps published CFG scale into the desk's internal seating coefficient.
const CFG_TO_TAU: f64 = 60.0;

struct CellOut {
    id: &'static str,
    hits: usize,
    nq: usize,
    nrows: usize,
    fid: f64,
    clip: f64,
}

struct Board {
    idx: u32,
    cfg: f64,
    sampler: String,
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
    let cfg = bind.cfg;
    let sampler = bind.sampler;
    let tau = cfg / CFG_TO_TAU;
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
        let fid = 100.0 * (1.0 - r10);
        let clip = gauge::agree(&qs, &qt, lot, tau);
        cells.push(CellOut {
            id,
            hits,
            nq,
            nrows: lot.rows.len(),
            fid,
            clip,
        });
    }
    Board {
        idx,
        cfg,
        sampler,
        cells,
    }
}

struct Band {
    f_lo: f64,
    f_hi: f64,
    c_lo: f64,
    c_hi: f64,
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
        if cols.len() < 5 {
            continue;
        }
        let vals: Vec<Option<f64>> = cols[1..5].iter().map(|c| c.parse::<f64>().ok()).collect();
        if vals.iter().any(|v| v.is_none()) {
            continue;
        }
        let v: Vec<f64> = vals.into_iter().map(|v| v.unwrap_or(0.0)).collect();
        out.insert(
            cols[0].to_string(),
            Band {
                f_lo: v[0],
                f_hi: v[1],
                c_lo: v[2],
                c_hi: v[3],
            },
        );
    }
    out
}

fn cfg_band(path: &Path) -> (f64, f64) {
    let Ok(text) = fs::read_to_string(path) else {
        return (7.40, 7.60);
    };
    for line in text.lines() {
        if let Some(idx) = line.find("CFG band is ") {
            let rest = &line[idx + "CFG band is ".len()..];
            let parts: Vec<&str> = rest.split(['–', '-']).map(|s| s.trim()).collect();
            if parts.len() >= 2 {
                let hi = parts[1].trim_end_matches(|c: char| !c.is_ascii_digit() && c != '.');
                if let (Ok(lo), Ok(hi)) = (parts[0].parse::<f64>(), hi.parse::<f64>()) {
                    return (lo, hi);
                }
            }
        }
    }
    (7.40, 7.60)
}

fn fmt6(v: f64) -> String {
    format!("{v:.6}")
}

fn run_eval(out_path: Option<PathBuf>) {
    let board = compute();
    let bands_path = app_root().join("docs/diff_bands.md");
    let bands = read_bands(&bands_path);
    let (cfg_lo, cfg_hi) = cfg_band(&bands_path);
    let mut ok = !board.cells.is_empty();
    if !(board.cfg >= cfg_lo && board.cfg <= cfg_hi) {
        ok = false;
    }
    for c in &board.cells {
        match bands.get(c.id) {
            Some(b) => {
                let fit = c.fid >= b.f_lo
                    && c.fid <= b.f_hi
                    && c.clip >= b.c_lo
                    && c.clip <= b.c_hi;
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
    s.push_str("{\"schema_tag\":\"diff-eval-v2\",\"scenarios\":[");
    for (i, c) in board.cells.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        let _ = write!(
            s,
            "{{\"id\":\"{}\",\"fid\":{},\"clip_score\":{},\"cfg_scale\":{},\"sampler\":\"{}\",\"tip_epoch\":{}}}",
            c.id,
            fmt6(c.fid),
            fmt6(c.clip),
            fmt6(board.cfg),
            board.sampler,
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
            fmt6(board.cfg)
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
