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

use crate::base::{data_paths, list_strata, read_ledger, read_roster, read_tasks};
use crate::decoy_p::roll_p;
use crate::decoy_q::hist_q;
use crate::emit_f::gate_y;

fn band_ok(task_id: &str, acc: f64) -> bool {
    let (lo, hi) = match task_id {
        "t_alpha" => (0.77, 0.79),
        "t_beta" => (0.690, 0.710),
        "t_gamma" => (0.71, 0.73),
        "t_delta" => (0.772, 0.792),
        _ => return acc.is_finite() && acc >= 0.0 && acc <= 1.0,
    };
    acc >= lo && acc <= hi
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut data = PathBuf::from("/app/data");
    let mut out = PathBuf::from("/output/cl-eval.json");
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
    let tasks = read_tasks(&paths.tasks);
    let strata = list_strata(&tasks);
    let roster = read_roster(&paths.roster);
    let ledger_rows = read_ledger(&paths.ledger);
    let ledger: Vec<(String, String, i64)> = ledger_rows
        .iter()
        .map(|r| (r.id.clone(), r.op.clone(), r.epoch))
        .collect();

    let (frac, tip_epoch) = pipe_a::resolve_tip(
        paths.journal.to_str().unwrap_or(""),
        paths.mirror.to_str().unwrap_or(""),
        paths.live.to_str().unwrap_or(""),
    );
    let flags = pipe_a::resolve_flags(&roster, &ledger, &strata, tip_epoch);

    let mut accs = Vec::with_capacity(tasks.len());
    let mut forgettings = Vec::with_capacity(tasks.len());
    let mut fracs = Vec::with_capacity(tasks.len());
    let mut actives = Vec::with_capacity(tasks.len());
    let mut rows_ok = !tasks.is_empty();

    for task in &tasks {
        let active = strata
            .iter()
            .zip(flags.iter())
            .find(|(s, _)| *s == &task.stratum)
            .map(|(_, f)| *f)
            .unwrap_or(true);
        let (acc, forg) = pipe_b::row_metrics(
            task.base,
            task.peak,
            task.durable_hit,
            task.overflow_hit,
            frac,
            tip_epoch,
            active,
        );
        if !band_ok(&task.id, acc) {
            rows_ok = false;
        }
        accs.push(acc);
        forgettings.push(forg);
        fracs.push(frac);
        actives.push(active);
    }

    let _ = hist_q(&accs);
    let _ = roll_p(&accs);

    let ok = gate_y(&accs, &forgettings, &fracs, &actives, rows_ok);

    let task_json: Vec<String> = tasks
        .iter()
        .zip(accs.iter())
        .zip(forgettings.iter())
        .map(|((task, acc), forg)| {
            format!(
                "{{\"id\":{},\"accuracy\":{:.12},\"forgetting\":{:.12},\"replay_frac\":{:.12},\"tip_epoch\":{}}}",
                json_str(&task.id),
                acc,
                forg,
                frac,
                tip_epoch
            )
        })
        .collect();

    let report = format!(
        "{{\n  \"schema_tag\": \"cl-eval-v1\",\n  \"tasks\": [{}],\n  \"eval_ok\": {}\n}}\n",
        task_json.join(", "),
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
