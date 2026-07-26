use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

use bevel_core::base::{self, FeatMap};
use bevel_core::pull;

const APP_ROOT: &str = "/app";
const FEATURES: [&str; 5] = ["f_amt", "f_age", "f_zip", "f_chn", "f_risk"];
const SLICES: [&str; 4] = ["retail", "corporate", "mobile", "holdout"];

fn app_root() -> PathBuf {
    match std::env::var("BEVEL_ROOT") {
        Ok(v) if !v.is_empty() => PathBuf::from(v),
        _ => PathBuf::from(APP_ROOT),
    }
}

fn load_slice(path: &Path) -> Vec<(f64, i32)> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut rows = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let y = base::extract_u32(line, "y").unwrap_or(0) as i32;
        let b = base::extract_f64(line, "base").unwrap_or(0.0);
        rows.push((b, y));
    }
    rows
}

fn skew_cap(name: &str) -> f64 {
    match name {
        "f_amt" => 0.020,
        "f_age" => 0.020,
        "f_zip" => 0.015,
        "f_chn" => 0.020,
        "f_risk" => 0.020,
        _ => 1.0,
    }
}

fn slice_band(id: &str) -> (f64, f64, f64, f64) {
    match id {
        "retail" => (0.66, 0.86, 0.18, 0.28),
        "corporate" => (0.66, 0.86, 0.18, 0.28),
        "mobile" => (0.66, 0.86, 0.18, 0.28),
        "holdout" => (0.66, 0.86, 0.18, 0.24),
        _ => (0.0, 1.0, 0.0, 1.0),
    }
}

fn fmt_num(v: f64) -> String {
    format!("{:.6}", v)
}

fn emit_report(out: &Path) {
    let root = app_root();
    let data = root.join("data");

    let rows = base::read_journal(&data.join("feature_registry/tip_journal.jsonl"));
    let tip = bevel_sx::desk::desk_tip(&rows, &data);
    let offline = base::offline_means(&data.join("offline/features.jsonl"));
    let online = pull::pull_m(&data, &tip);
    let shadow = pull::pull_shadow(&data);
    let sel = base::read_selection(&root.join("calib/trial_pref.toml"));
    let bound = pull::blend(&online, &shadow, &sel);
    let source = bevel_sx::desk::desk_tag(&tip);

    let mut feat_json = String::from("[");
    let mut ok = true;
    for (i, name) in FEATURES.iter().enumerate() {
        let off_m = offline.get(*name).copied().unwrap_or(0.0);
        let on_m = online.get(*name).copied().unwrap_or(0.0);
        let skew = bevel_sx::desk::desk_gap(off_m, on_m);
        if skew.abs() > skew_cap(name) {
            ok = false;
        }
        if i > 0 {
            feat_json.push(',');
        }
        feat_json.push_str(&format!(
            "{{\"name\":\"{name}\",\"offline_mean\":{off},\"online_mean\":{on},\"skew\":{sk},\"source\":\"{src}\"}}",
            off = fmt_num(off_m),
            on = fmt_num(on_m),
            sk = fmt_num(skew),
            src = source
        ));
    }
    feat_json.push(']');

    let shift = base::cal_term(&bound, &offline);
    let mut slice_json = String::from("[");
    for (i, sid) in SLICES.iter().enumerate() {
        let raw = load_slice(&data.join("slices").join(format!("{sid}.jsonl")));
        let pairs: Vec<(f64, i32)> = raw
            .into_iter()
            .map(|(b, y)| (base::sigmoid(b + shift), y))
            .collect();
        let a = base::auc(&pairs);
        let br = base::brier(&pairs);
        let (alo, ahi, blo, bhi) = slice_band(sid);
        if !(alo <= a && a <= ahi && blo <= br && br <= bhi) {
            ok = false;
        }
        if i > 0 {
            slice_json.push(',');
        }
        slice_json.push_str(&format!(
            "{{\"id\":\"{sid}\",\"auc\":{a},\"brier\":{b}}}",
            a = fmt_num(a),
            b = fmt_num(br)
        ));
    }
    slice_json.push(']');

    let durable_tip = rows.iter().any(|r| r.tip == tip && r.state == "durable");
    if !durable_tip || source != tip || tip.is_empty() {
        ok = false;
    }

    let body = format!(
        "{{\n  \"schema_tag\": \"feature-eval/v1\",\n  \"features\": {feat_json},\n  \"slices\": {slice_json},\n  \"calibration_ok\": {ok}\n}}\n",
        ok = if ok { "true" } else { "false" }
    );

    if let Some(parent) = out.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let mut f = fs::File::create(out).expect("create report");
    f.write_all(body.as_bytes()).expect("write report");
}

fn main() {
    let mut args = std::env::args().skip(1);
    let cmd = args.next().unwrap_or_default();
    match cmd.as_str() {
        "eval" => {
            let mut out = PathBuf::from("/output/feature-eval.json");
            while let Some(a) = args.next() {
                if a == "--out" {
                    if let Some(p) = args.next() {
                        out = PathBuf::from(p);
                    }
                }
            }
            emit_report(&out);
        }
        _ => {
            eprintln!("usage: bevel eval --out <path>");
            std::process::exit(2);
        }
    }
}

// silence unused import warning path in some builds
#[allow(dead_code)]
fn _touch_featmap(_: &FeatMap) {}
