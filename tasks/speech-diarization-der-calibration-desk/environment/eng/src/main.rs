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

use crate::base::data_paths;
use crate::base::read_slices;
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn band_ok(slice_id: &str, der: f64, jer: f64) -> bool {
    let (dlo, dhi, jlo, jhi) = match slice_id {
        "s_meet_a" => (0.092, 0.104, 0.126, 0.138),
        "s_meet_b" => (0.106, 0.118, 0.142, 0.154),
        "s_call_c" => (0.081, 0.093, 0.115, 0.127),
        "s_call_d" => (0.119, 0.131, 0.155, 0.167),
        "s_far_e" => (0.135, 0.147, 0.172, 0.184),
        _ => return der.is_finite() && jer.is_finite(),
    };
    der >= dlo && der <= dhi && jer >= jlo && jer <= jhi
}

fn durable_method(m: &str) -> bool {
    matches!(m, "ahc" | "spectral" | "nme")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/diar-eval.json");
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
    let slices = read_slices(&paths.audio);

    let tip = pipe_a::resolve_tip(
        paths.embed_journal.to_str().unwrap_or(""),
        paths.embed_retired.to_str().unwrap_or(""),
        "",
    );
    let method = pipe_a::resolve_method(
        paths.cluster_journal.to_str().unwrap_or(""),
        paths.cluster_retired.to_str().unwrap_or(""),
        "",
    );

    let mut ders = Vec::with_capacity(slices.len());
    let mut jers = Vec::with_capacity(slices.len());
    let mut methods = Vec::with_capacity(slices.len());
    let mut rows_ok = !slices.is_empty();

    for s in &slices {
        let (der, jer) = pipe_b::row_metrics(s, &method.clustering, tip.epoch);
        if !band_ok(&s.id, der, jer) {
            rows_ok = false;
        }
        if !durable_method(&method.clustering) {
            rows_ok = false;
        }
        ders.push(der);
        jers.push(jer);
        methods.push(method.clustering.clone());
    }

    let _ = hist_q(&jers);
    let _ = roll_p(&ders);

    let ok = gate_y(&ders, &jers, &methods, rows_ok);

    let slice_json: Vec<String> = slices
        .iter()
        .zip(ders.iter())
        .zip(jers.iter())
        .map(|((s, der), jer)| {
            format!(
                "{{\"id\":{},\"der\":{:.12},\"jer\":{:.12},\"clustering\":{},\"tip_epoch\":{}}}",
                json_str(&s.id),
                der,
                jer,
                json_str(&method.clustering),
                tip.epoch
            )
        })
        .collect();

    let report = format!(
        "{{\n  \"schema_tag\": \"diar-eval-v1\",\n  \"slices\": [{}],\n  \"eval_ok\": {}\n}}\n",
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
