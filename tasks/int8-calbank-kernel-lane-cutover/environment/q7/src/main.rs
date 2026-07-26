#[allow(dead_code)]
mod decoy_tip;
mod emit_z;
mod knit_q;
mod run_a;
mod run_b;
mod run_c;
mod slot_v;

use emit_z::{emit_z, Row};
use serde::Deserialize;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;

#[derive(Deserialize)]
struct Tip {
    epoch: u32,
    sealed: Option<bool>,
}

#[derive(Deserialize)]
struct ResumePack {
    epoch: u32,
}

#[derive(Deserialize)]
struct Scenario {
    id: String,
    salt: u32,
    mask: Vec<u8>,
    fallback: i32,
    resume: bool,
}

fn lane_name(idx: i32) -> String {
    match idx {
        0 => "k0".to_string(),
        1 => "k1".to_string(),
        2 => "k2".to_string(),
        _ => format!("k{idx}"),
    }
}

fn bytes_eq_trim(a: &[u8], b: &[u8]) -> bool {
    let ta = a
        .iter()
        .copied()
        .filter(|c| *c != b'\n' && *c != b'\r' && *c != b' ')
        .collect::<Vec<_>>();
    let tb = b
        .iter()
        .copied()
        .filter(|c| *c != b'\n' && *c != b'\r' && *c != b' ')
        .collect::<Vec<_>>();
    ta == tb
}

fn fence_matches(root: &Path) -> u8 {
    let got = fs::read(root.join("x7/slot_s.dat")).unwrap_or_default();
    let want = fs::read(root.join("x7/want.dat")).unwrap_or_default();
    if !want.is_empty() && bytes_eq_trim(&got, &want) {
        1
    } else {
        0
    }
}

fn profile_name_ok(path: &Path) -> bool {
    let name = match path.file_name().and_then(|s| s.to_str()) {
        Some(n) => n,
        None => return false,
    };
    let b = name.as_bytes();
    b.len() >= 4
        && b[0].is_ascii_digit()
        && b[1].is_ascii_digit()
        && b[2] == b'-'
        && name.ends_with(".toml")
}

fn gen_floor(root: &Path) -> u32 {
    let text = fs::read_to_string(root.join("config/runtime.toml")).unwrap_or_default();
    let mut floor = 2u32;
    let mut in_codec = false;
    for line in text.lines() {
        let t = line.trim();
        if t.starts_with('[') {
            in_codec = t == "[codec]";
            continue;
        }
        if in_codec {
            if let Some(rest) = t.strip_prefix("gen_floor") {
                let rest = rest.trim().trim_start_matches('=').trim();
                if let Ok(v) = rest.parse::<u32>() {
                    floor = v;
                }
            }
        }
    }
    floor
}

fn fold_codec(root: &Path) -> u8 {
    let dir = root.join("config/profiles");
    let mut hot: u8 = 0;
    let mut gen: u32 = 0;
    let mut entries: Vec<_> = fs::read_dir(&dir)
        .map(|rd| rd.filter_map(|e| e.ok()).map(|e| e.path()).collect())
        .unwrap_or_default();
    entries.sort();
    for path in entries {
        if !profile_name_ok(&path) {
            continue;
        }
        if let Ok(text) = fs::read_to_string(&path) {
            for line in text.lines() {
                let t = line.trim();
                if let Some(rest) = t.strip_prefix("hot") {
                    let rest = rest.trim().trim_start_matches('=').trim();
                    if rest == "1" || rest == "true" {
                        hot = 1;
                    } else if rest == "0" || rest == "false" {
                        hot = 0;
                    }
                }
                if let Some(rest) = t.strip_prefix("gen") {
                    let rest = rest.trim().trim_start_matches('=').trim();
                    if let Ok(v) = rest.parse::<u32>() {
                        gen = v;
                    }
                }
            }
        }
    }
    let floor = gen_floor(root);
    if hot != 0 && gen >= floor {
        1
    } else {
        0
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let out = args
        .get(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/output/eval-ledger.json"));
    let root = PathBuf::from(env::var("APP_ROOT").unwrap_or_else(|_| "/app".into()));

    let live: Tip = serde_json::from_str(
        &fs::read_to_string(root.join("data/banks/tip_live.json")).expect("tip_live"),
    )
    .expect("tip_live json");
    let durable: Tip = serde_json::from_str(
        &fs::read_to_string(root.join("data/banks/tip_durable.json")).expect("tip_durable"),
    )
    .expect("tip_durable json");

    let fence = fence_matches(&root);
    let tip_sealed: u8 = if durable.sealed.unwrap_or(false) && fence != 0 {
        1
    } else {
        0
    };
    let bound = run_a::bound_epoch(live.epoch, durable.epoch, tip_sealed);

    let pack: ResumePack = serde_json::from_str(
        &fs::read_to_string(root.join("data/checkpoints/resume_pack.json")).expect("resume"),
    )
    .expect("resume json");

    let scenarios: Vec<Scenario> = serde_json::from_str(
        &fs::read_to_string(root.join("data/eval/scenarios.json")).expect("scenarios"),
    )
    .expect("scenarios json");

    let hot = fold_codec(&root);

    let mut rows = Vec::new();
    for sc in scenarios {
        let mask_view: Vec<u8> = if hot != 0 {
            sc.mask.clone()
        } else {
            vec![0u8; sc.mask.len()]
        };
        let lane_idx = run_b::pick_lane(&mask_view, sc.fallback);
        let any_live = mask_view.iter().any(|&m| m != 0);
        let mixed: i32 = if !any_live && lane_idx == sc.fallback {
            1
        } else {
            0
        };
        let epoch = if sc.resume {
            let rebased = root.join("data/checkpoints/rebase.stamp").is_file();
            if rebased {
                run_c::epoch_after(pack.epoch, bound, 1)
            } else {
                run_c::epoch_after(pack.epoch, bound, 0)
            }
        } else {
            run_c::epoch_after(bound, bound, 0)
        };
        let top1 = run_b::score(epoch, lane_idx, mixed, sc.salt);
        rows.push(Row {
            id: sc.id,
            lane: lane_name(lane_idx),
            mode: if mixed == 1 {
                "mixed".to_string()
            } else {
                "int8".to_string()
            },
            top1,
        });
    }

    if let Err(e) = emit_z(&out, bound, rows) {
        eprintln!("emit failed: {e}");
        process::exit(1);
    }
}
