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

use crate::base::{data_paths, list_expert_ids, load_slices, read_caps, read_hold, read_ledger};
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn band_ok(slice_id: &str, ppl: f64) -> bool {
    let (lo, hi) = match slice_id {
        "s_alpha" => (2.693562, 2.860174),
        "s_beta" => (1.853196, 1.967826),
        "s_gamma" => (2.091763, 2.221150),
        "s_delta" => (2.602896, 2.763900),
        _ => return ppl.is_finite() && ppl > 1.0 && ppl < 8.0,
    };
    ppl >= lo && ppl <= hi
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/moe-eval.json");
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
    let ids = list_expert_ids(&paths.experts);
    let caps = read_caps(&paths.experts, &ids);
    let roster = read_hold(&paths.roster);
    let ledger = read_ledger(&paths.ledger);
    let slices = load_slices(&paths.eval);

    let (scale, tip_epoch) = pipe_a::resolve_scale(
        paths.journal.to_str().unwrap_or(""),
        paths.mirror.to_str().unwrap_or(""),
        paths.live.to_str().unwrap_or(""),
    );
    let flags = pipe_a::resolve_flags(&roster, &ledger, &ids, tip_epoch);

    let mut slice_json = Vec::new();
    let mut agg = vec![0.0_f64; ids.len()];
    let mut rows_ok = !slices.is_empty();

    for row in &slices {
        let (weights, ppl, ent) = pipe_b::row_metrics(&row.logits, &caps, &flags, scale);
        if weights.len() == agg.len() {
            for (a, w) in agg.iter_mut().zip(weights.iter()) {
                *a += *w;
            }
        }
        if !band_ok(&row.id, ppl) {
            rows_ok = false;
        }
        slice_json.push(format!(
            "{{\"id\":{},\"perplexity\":{:.12},\"expert_entropy\":{:.12},\"router_temp\":{:.12}}}",
            json_str(&row.id),
            ppl,
            ent,
            scale
        ));
    }

    let n = slices.len().max(1) as f64;
    for a in agg.iter_mut() {
        *a /= n;
    }

    let _ = hist_q(&agg);
    let _ = roll_p(&agg);

    let experts_json: Vec<String> = ids
        .iter()
        .zip(agg.iter())
        .zip(flags.iter())
        .map(|((id, share), flag)| {
            format!(
                "{{\"id\":{},\"load_share\":{:.12},\"active\":{}}}",
                json_str(id),
                share,
                if *flag { "true" } else { "false" }
            )
        })
        .collect();

    let ok = gate_y(&agg, &flags, rows_ok);
    let report = format!(
        "{{\n  \"schema_tag\": \"moe-eval-v1\",\n  \"experts\": [{}],\n  \"slices\": [{}],\n  \"eval_ok\": {}\n}}\n",
        experts_json.join(", "),
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
