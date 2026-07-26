use std::fs;
use std::io::Write as _;
use std::path::{Path, PathBuf};

use loam_core::base::{self, Lot};
use loam_core::gauge;
use loam_core::lens;
use loam_core::weave;
use loam_rank::knot;
use loam_rank::lace;

const APP_ROOT: &str = "/app";

fn app_root() -> PathBuf {
    match std::env::var("LOAM_ROOT") {
        Ok(v) if !v.is_empty() => PathBuf::from(v),
        _ => PathBuf::from(APP_ROOT),
    }
}

fn empty_lot(name: &str) -> Lot {
    Lot {
        name: name.to_string(),
        feats: Vec::new(),
        labels: Vec::new(),
        edges: Vec::new(),
    }
}

fn load_graph(root: &Path, id: u32) -> Lot {
    let name = format!("graph_{id:02}");
    base::read_graph(&root.join("graphs").join(format!("{name}.gbin")), &name)
}

struct Band {
    a_lo: f64,
    a_hi: f64,
    f_lo: f64,
    f_hi: f64,
}

fn bands() -> [(&'static str, Band); 6] {
    [
        ("cold_a", Band { a_lo: 0.600, a_hi: 0.640, f_lo: 0.970, f_hi: 1.001 }),
        ("resume_a", Band { a_lo: 0.600, a_hi: 0.640, f_lo: 0.970, f_hi: 1.001 }),
        ("cold_b", Band { a_lo: 0.600, a_hi: 0.640, f_lo: 0.990, f_hi: 1.001 }),
        ("resume_b", Band { a_lo: 0.600, a_hi: 0.640, f_lo: 0.990, f_hi: 1.001 }),
        ("mix_c", Band { a_lo: 0.640, a_hi: 0.675, f_lo: 0.990, f_hi: 1.001 }),
        ("mix_d", Band { a_lo: 0.560, a_hi: 0.605, f_lo: 0.990, f_hi: 1.001 }),
    ]
}

fn emit_eval(out: &Path) {
    let root = app_root().join("data");
    let marks = base::read_marks(&root.join("feature_registry/tip_journal.jsonl"));
    let retired = knot::read_retired(&root.join("feature_registry/retired_tips.jsonl"));
    let bind = lace::lace_b(&marks, &root, &retired);
    let idx = bind.idx;
    let agg = bind.agg.clone();
    let pref = bind.norm.clone();

    let lots: Vec<Lot> = (1..=8).map(|i| load_graph(&root, i)).collect();
    let fam_a = base::fold_graphs(&lots[0..4], "a");
    let fam_b = base::fold_graphs(&lots[4..8], "b");
    let mixed = weave::weave_m(&marks, &lots, &retired);
    let (mix_c, mix_d) = if mixed.len() == 2 {
        (mixed[0].clone(), mixed[1].clone())
    } else {
        (empty_lot("c"), empty_lot("d"))
    };

    let load = |n: &str| base::read_blob(&root.join("checkpoints").join(n));
    let plan: Vec<(&str, Vec<u8>, &Lot)> = vec![
        ("cold_a", load("cold_a.ckpt"), &fam_a),
        ("resume_a", load("resume_a.ckpt"), &fam_a),
        ("cold_b", load("cold_b.ckpt"), &fam_b),
        ("resume_b", load("resume_b.ckpt"), &fam_b),
        ("mix_c", load("resume_a.ckpt"), &mix_c),
        ("mix_d", load("resume_b.ckpt"), &mix_d),
    ];

    let mut cells: Vec<(String, f64, f64)> = Vec::new();
    for (id, blob, lot) in plan {
        let weights = lens::lens_unfold(&blob);
        let (acc, f1) = gauge::score_lot(lot, &weights, &agg, &pref);
        cells.push((id.to_string(), acc, f1));
    }

    let band_table = bands();
    let mut bands_ok = true;
    for (id, acc, f1) in &cells {
        if let Some((_, b)) = band_table.iter().find(|(n, _)| n == id) {
            if !(b.a_lo <= *acc && *acc <= b.a_hi && b.f_lo <= *f1 && *f1 <= b.f_hi) {
                bands_ok = false;
            }
        } else {
            bands_ok = false;
        }
    }

    let mut body = String::new();
    body.push_str("{\n");
    body.push_str("  \"schema_tag\": \"gnn-eval-v2\",\n");
    body.push_str("  \"scenarios\": [\n");
    for (i, (id, acc, f1)) in cells.iter().enumerate() {
        body.push_str("    {\n");
        body.push_str(&format!("      \"id\": \"{id}\",\n"));
        body.push_str(&format!("      \"accuracy\": {acc:.6},\n"));
        body.push_str(&format!("      \"macro_f1\": {f1:.6},\n"));
        body.push_str(&format!("      \"agg\": \"{agg}\",\n"));
        body.push_str(&format!("      \"tip_epoch\": {idx}\n"));
        if i + 1 == cells.len() {
            body.push_str("    }\n");
        } else {
            body.push_str("    },\n");
        }
    }
    body.push_str("  ],\n");
    body.push_str(&format!("  \"bands_ok\": {}\n", if bands_ok { "true" } else { "false" }));
    body.push_str("}\n");

    if let Some(parent) = out.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let mut f = fs::File::create(out).expect("create out");
    f.write_all(body.as_bytes()).expect("write out");
}

fn main() {
    let mut args = std::env::args().skip(1);
    let cmd = args.next().unwrap_or_default();
    match cmd.as_str() {
        "eval" => {
            let mut out = PathBuf::from("/output/gnn-eval.json");
            while let Some(a) = args.next() {
                if a == "--out" {
                    if let Some(p) = args.next() {
                        out = PathBuf::from(p);
                    }
                }
            }
            emit_eval(&out);
        }
        "trace" => {
            let root = app_root();
            let s = loam_rank::dial::dial_stride(&root);
            println!("stride={s}");
        }
        _ => {
            eprintln!("usage: loam eval --out PATH");
            std::process::exit(2);
        }
    }
}
