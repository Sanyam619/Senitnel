#[path = "../../seat/knit_b.rs"]
mod knit_b;
#[path = "../../flag/xv_c.rs"]
mod xv_c;
#[path = "../../mix/ward_d.rs"]
mod ward_d;
#[path = "../../score/helm_e.rs"]
mod helm_e;
#[path = "../../gate/emit_f.rs"]
mod emit_f;

mod base;
mod decoy_p;
mod decoy_q;
mod pipe_a;
mod pipe_b;

use std::env;
use std::fs;
use std::path::PathBuf;

use crate::base::{data_paths, load_scenarios, read_live_cap, read_schedule};
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn depth_band(depth: f64) -> bool {
    depth >= 4.35 && depth <= 4.65
}

fn ppl_band(id: &str, ppl: f64) -> bool {
    let (lo, hi) = match id {
        "cold_a" | "resume_a" => (4.155, 4.325),
        "cold_b" | "resume_b" => (5.075, 5.282),
        "mix_c" => (3.648, 3.798),
        "mix_d" => (4.732, 4.925),
        _ => return ppl.is_finite() && ppl > 1.0 && ppl < 20.0,
    };
    ppl >= lo && ppl <= hi
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/mod-eval.json");
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--data" => {
                i += 1;
                data = PathBuf::from(&args[i]);
            }
            "--out" => {
                i += 1;
                out = PathBuf::from(&args[i]);
            }
            _ => {}
        }
        i += 1;
    }

    let paths = data_paths(&data);
    let scenarios = load_scenarios(&paths.eval);
    let pick = pipe_a::resolve_tip(
        paths.journal.to_str().unwrap_or(""),
        paths.retired.to_str().unwrap_or(""),
        paths.live.to_str().unwrap_or(""),
    );
    let live_cap = read_live_cap(&paths.live);
    let seated_cap = pipe_a::resolve_cap(pick.capacity, live_cap, &pick.tip);
    let (shallow, deep) = read_schedule(&paths.schedule, seated_cap);

    let mut scen_json = Vec::new();
    let mut depths = Vec::new();
    let mut ppls = Vec::new();
    let mut caps = Vec::new();
    let mut rows_ok = !scenarios.is_empty();

    for row in &scenarios {
        // Depth follows the capacity scalar; perplexity follows tip
        // capacity with mode-sensitive resume handling inside score_u.
        let (depth, _) = pipe_b::row_metrics(
            &row.token_scores,
            row.base_nll,
            seated_cap,
            shallow,
            deep,
            &row.mode,
            live_cap,
        );
        let ppl = crate::helm_e::score_u(row.base_nll, pick.capacity, &row.mode, live_cap);

        if !depth_band(depth) || !ppl_band(&row.id, ppl) {
            rows_ok = false;
        }
        depths.push(depth);
        ppls.push(ppl);
        caps.push(seated_cap);
        scen_json.push(format!(
            "{{\"id\":{},\"perplexity\":{:.12},\"avg_depth\":{:.12},\"capacity\":{:.12},\"tip_epoch\":{}}}",
            json_str(&row.id),
            ppl,
            depth,
            seated_cap,
            pick.epoch
        ));
    }

    let _ = hist_q(&depths);
    let _ = roll_p(&ppls);

    let ok = gate_y(&depths, &ppls, &caps, rows_ok);
    let report = format!(
        "{{\n  \"schema_tag\": \"mod-eval-v1\",\n  \"scenarios\": [{}],\n  \"bands_ok\": {}\n}}\n",
        scen_json.join(", "),
        if ok { "true" } else { "false" }
    );

    if let Some(parent) = out.parent() {
        let _ = fs::create_dir_all(parent);
    }
    fs::write(&out, report).expect("write report");
}

fn json_str(s: &str) -> String {
    format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\""))
}
