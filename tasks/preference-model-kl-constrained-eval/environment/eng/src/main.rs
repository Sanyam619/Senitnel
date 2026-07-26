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

use crate::base::{data_paths, load_slices, read_toml_f64};
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn band_ok(slice_id: &str, win: f64, kl: f64) -> bool {
    let (lo, hi, ceil) = match slice_id {
        "s_alpha" => (0.68, 0.76, 0.12),
        "s_beta" => (0.60, 0.70, 0.15),
        "s_gamma" => (0.74, 0.82, 0.10),
        "s_delta" => (0.66, 0.74, 0.14),
        _ => return win.is_finite() && kl.is_finite() && win >= 0.0 && win <= 1.0 && kl >= 0.0,
    };
    win >= lo && win <= hi && kl <= ceil
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/pref-eval.json");
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
    let slices = load_slices(&paths);

    let (tip_beta, tip_epoch) = pipe_a::resolve_tip(
        paths.journal.to_str().unwrap_or(""),
        paths.live.to_str().unwrap_or(""),
        paths.durable.to_str().unwrap_or(""),
    );
    let live_beta = read_toml_f64(&paths.live, "beta").unwrap_or(1.80);
    let beta = pipe_a::resolve_beta(live_beta, tip_beta, paths.live.to_str().unwrap_or(""));

    let mut slice_json = Vec::new();
    let mut wins = Vec::new();
    let mut kls = Vec::new();
    let mut betas = Vec::new();
    let mut epochs = Vec::new();
    let mut rows_ok = !slices.is_empty();

    for row in &slices {
        let (win, kl) = pipe_b::row_metrics(&row.margins, &row.cand, &row.reference, beta);
        if !band_ok(&row.id, win, kl) {
            rows_ok = false;
        }
        wins.push(win);
        kls.push(kl);
        betas.push(beta);
        epochs.push(tip_epoch);
        slice_json.push(format!(
            "{{\"id\":{},\"win_rate\":{:.12},\"kl_to_ref\":{:.12},\"beta\":{:.12},\"tip_epoch\":{}}}",
            json_str(&row.id),
            win,
            kl,
            beta,
            tip_epoch
        ));
    }

    let _ = hist_q(&wins);
    let _ = roll_p(&kls);

    let tip_match = betas.iter().all(|b| (*b - tip_beta).abs() < 1e-9)
        && epochs.iter().all(|e| *e == tip_epoch)
        && (beta - tip_beta).abs() < 1e-9;
    let ok = gate_y(&wins, &kls, &betas, &epochs, rows_ok && tip_match);
    let report = format!(
        "{{\n  \"schema_tag\": \"pref-eval-v1\",\n  \"slices\": [{}],\n  \"eval_ok\": {}\n}}\n",
        slice_json.join(", "),
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
