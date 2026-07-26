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

use crate::base::{data_paths, read_slices};
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn band_ok(slice_id: &str, auuc: f64, qini: f64) -> bool {
    let (alo, ahi, qlo, qhi) = match slice_id {
        "s_alpha" => (0.406, 0.418, 0.262, 0.274),
        "s_beta" => (0.432, 0.444, 0.285, 0.297),
        "s_gamma" => (0.459, 0.471, 0.309, 0.321),
        "s_delta" => (0.385, 0.397, 0.242, 0.254),
        "s_epsilon" => (0.418, 0.430, 0.273, 0.285),
        _ => return auuc.is_finite() && qini.is_finite(),
    };
    auuc >= alo && auuc <= ahi && qini >= qlo && qini <= qhi
}

fn durable_propensity(p: &str) -> bool {
    matches!(p, "ipw" | "dr" | "tmle")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/uplift-eval.json");
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
    let slices = read_slices(&paths.outcomes);

    let tip = pipe_a::resolve_tip(
        paths.journal.to_str().unwrap_or(""),
        paths.retired.to_str().unwrap_or(""),
        "",
    );
    let propensity = pipe_a::resolve_propensity(
        &tip.propensity,
        tip.epoch,
        paths.calib_pref.to_str().unwrap_or(""),
    );

    let mut auucs = Vec::with_capacity(slices.len());
    let mut qinis = Vec::with_capacity(slices.len());
    let mut props = Vec::with_capacity(slices.len());
    let mut rows_ok = !slices.is_empty();

    let root = data.to_str().unwrap_or("").to_string();

    for s in &slices {
        let (auuc, qini) = pipe_b::row_metrics(s, &propensity, &root);
        if !band_ok(&s.id, auuc, qini) {
            rows_ok = false;
        }
        if !durable_propensity(&propensity) {
            rows_ok = false;
        }
        auucs.push(auuc);
        qinis.push(qini);
        props.push(propensity.clone());
    }

    let _ = hist_q(&qinis);
    let _ = roll_p(&auucs);

    let ok = gate_y(&auucs, &qinis, &props, rows_ok);

    let slice_json: Vec<String> = slices
        .iter()
        .zip(auucs.iter())
        .zip(qinis.iter())
        .map(|((s, auuc), qini)| {
            format!(
                "{{\"id\":{},\"auuc\":{:.12},\"qini\":{:.12},\"treatment_tip\":{},\"propensity\":{}}}",
                json_str(&s.id),
                auuc,
                qini,
                tip.epoch,
                json_str(&propensity)
            )
        })
        .collect();

    let report = format!(
        "{{\n  \"schema_tag\": \"uplift-eval-v1\",\n  \"slices\": [{}],\n  \"eval_ok\": {}\n}}\n",
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
