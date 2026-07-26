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

use crate::base::{data_paths, read_windows};
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn band_ok(window_id: &str, smape: f64, mase: f64) -> bool {
    let (slo, shi, mlo, mhi) = match window_id {
        "w_alpha" => (0.136, 0.148, 0.870, 0.890),
        "w_beta" => (0.150, 0.162, 0.900, 0.920),
        "w_gamma" => (0.162, 0.174, 0.935, 0.955),
        "w_delta" => (0.128, 0.140, 0.850, 0.870),
        "w_epsilon" => (0.145, 0.157, 0.885, 0.905),
        _ => return smape.is_finite() && mase.is_finite(),
    };
    smape >= slo && smape <= shi && mase >= mlo && mase <= mhi
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/forecast-eval.json");
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
    let windows = read_windows(&paths.series);

    let tip = pipe_a::resolve_tip(
        paths.journal.to_str().unwrap_or(""),
        paths.retired.to_str().unwrap_or(""),
        "",
    );
    let scaler = pipe_a::resolve_scaler(
        &tip.scaler,
        tip.epoch,
        paths.calib_pref.to_str().unwrap_or(""),
    );

    let mut smapes = Vec::with_capacity(windows.len());
    let mut mases = Vec::with_capacity(windows.len());
    let mut scalers = Vec::with_capacity(windows.len());
    let mut rows_ok = !windows.is_empty();

    for w in &windows {
        let (smape, mase) = pipe_b::row_metrics(
            w.smape_causal,
            w.mase_causal,
            w.smape_leak,
            w.mase_leak,
            tip.shift,
            tip.epoch,
            tip.horizon,
        );
        if !band_ok(&w.id, smape, mase) {
            rows_ok = false;
        }
        if scaler != "train_only" {
            rows_ok = false;
        }
        smapes.push(smape);
        mases.push(mase);
        scalers.push(scaler.clone());
    }

    let _ = hist_q(&mases);
    let _ = roll_p(&smapes);

    let ok = gate_y(&smapes, &mases, &scalers, rows_ok);

    let window_json: Vec<String> = windows
        .iter()
        .zip(smapes.iter())
        .zip(mases.iter())
        .map(|((w, smape), mase)| {
            format!(
                "{{\"id\":{},\"smape\":{:.12},\"mase\":{:.12},\"horizon\":{},\"split_tip\":{},\"scaler\":{}}}",
                json_str(&w.id),
                smape,
                mase,
                tip.horizon,
                tip.epoch,
                json_str(&scaler)
            )
        })
        .collect();

    let report = format!(
        "{{\n  \"schema_tag\": \"forecast-eval-v1\",\n  \"windows\": [{}],\n  \"eval_ok\": {}\n}}\n",
        window_json.join(", "),
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
