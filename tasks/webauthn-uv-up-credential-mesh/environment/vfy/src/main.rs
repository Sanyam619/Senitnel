mod emit_c;
mod fold_a;
mod sieve_b;
mod skim_fold;
mod skim_sieve;

use std::collections::HashMap;
use std::fs;
use std::path::Path;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() >= 2 && args[1] == "attest" {
        let out = parse_out(&args).unwrap_or_else(|| "/output/ceremony-ledger.json".to_string());
        run_attest(&out);
        return;
    }
    eprintln!("usage: trusteval attest [--out path]");
    std::process::exit(2);
}

fn run_attest(out: &str) {
    let policy = fold_a::load_policy();
    let manifest = fold_a::resolve_manifest(&policy);
    let marks = fold_a::load_watermarks(&manifest);
    let nonces = fold_a::load_nonces(&manifest);
    let revocations = skim_sieve::load_ledger();
    let profiles = skim_fold::load_profiles();
    let matrix = skim_fold::load_matrix();
    let uv_policy = skim_fold::load_uv_policy();
    let stream_order = load_state_token("stream.order");
    let hold_bound = load_state_token("hold_bound");
    let exclusive_hold = hold_bound.trim() == "exclusive";

    let mut pending: Vec<skim_fold::Frame> = Vec::new();
    let mut quarantine: Vec<emit_c::QuarantineEntry> = Vec::new();

    let cred_dir = Path::new(lattice_core::CREDENTIALS_DIR);
    for lane_name in &["mqtt", "lora", "uart", "canbus", "zigbee"] {
        let path = cred_dir.join(format!("{}.jsonl", lane_name));
        if path.exists() {
            pending.extend(skim_fold::load_jsonl_lane(&path, lane_name));
        }
    }

    let wal_dir = Path::new(lattice_core::SEGMENTS_DIR);
    if let Ok(entries) = fs::read_dir(&wal_dir) {
        let mut paths: Vec<_> = entries
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.extension().map_or(false, |ext| ext == "bin"))
            .collect();
        paths.sort();
        for path in paths {
            let Ok(raw) = fs::read(&path) else {
                continue;
            };
            let (accepted, rejected) = sieve_b::decode_wal_with_quarantine(&raw, &nonces);
            quarantine.extend(rejected);
            pending.extend(accepted);
        }
    }

    let interleave = stream_order.trim() == "interleave-asc";
    if interleave {
        // JSONL ∪ WAL by ascending timestamp; equal-ts prefers WAL first.
        pending.sort_by(|a, b| {
            (a.epoch, a.lane.as_str(), a.ts, !a.from_wal).cmp(&(
                b.epoch,
                b.lane.as_str(),
                b.ts,
                !b.from_wal,
            ))
        });
    } else {
        // Process JSONL then WAL as separate passes (no shared fence).
        pending.sort_by(|a, b| {
            (a.from_wal, a.epoch, a.lane.as_str(), a.ts).cmp(&(
                b.from_wal,
                b.epoch,
                b.lane.as_str(),
                b.ts,
            ))
        });
    }

    let mut all_frames: Vec<skim_fold::Frame> = Vec::new();
    let mut max_ts: HashMap<(u16, String), u64> = HashMap::new();
    if policy.replay_protection == "monotonic" && interleave {
        for f in pending {
            let key = (f.epoch, f.lane.clone());
            let prev = max_ts.get(&key).copied().unwrap_or(0);
            if prev > 0 && f.ts <= prev {
                if f.from_wal {
                    quarantine.push(emit_c::QuarantineEntry {
                        epoch: f.epoch,
                        lane: f.lane.clone(),
                        ts: f.ts,
                        reason: "replay".to_string(),
                    });
                }
            } else {
                max_ts.insert(key, f.ts);
                all_frames.push(f);
            }
        }
    } else {
        // No cross-stream replay fence when stream.order is not interleave-asc.
        all_frames = pending;
    }

    let filtered: Vec<skim_fold::Frame> = all_frames
        .into_iter()
        .filter(|f| {
            let mark = marks.get(&f.epoch).copied().unwrap_or(0);
            f.ts <= mark
        })
        .collect();

    let classified = skim_sieve::classify(&filtered, &revocations, exclusive_hold);
    for cf in &classified {
        if cf.status == skim_sieve::FrameStatus::Revoked && cf.from_wal {
            quarantine.push(emit_c::QuarantineEntry {
                epoch: cf.epoch,
                lane: cf.lane.clone(),
                ts: cf.ts,
                reason: "revoked".to_string(),
            });
        }
    }

    let roster = skim_fold::evaluate(&classified, &profiles, &matrix, &uv_policy);

    if let Err(e) = emit_c::write_roster(out, &roster) {
        eprintln!("emit failed: {e}");
        std::process::exit(1);
    }

    let quarantine_path = out.replace("ceremony-ledger", "quarantine");
    let quarantine_path = if quarantine_path == *out {
        let p = Path::new(out).parent().unwrap_or(Path::new("/output"));
        p.join("quarantine.json").to_string_lossy().into_owned()
    } else {
        quarantine_path
    };
    if let Err(e) = emit_c::write_quarantine(&quarantine_path, &quarantine) {
        eprintln!("quarantine emit failed: {e}");
        std::process::exit(1);
    }
}

fn load_state_token(name: &str) -> String {
    let path = Path::new(lattice_core::CEREMONY_VAR).join("state").join(name);
    fs::read_to_string(&path)
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn parse_out(args: &[String]) -> Option<String> {
    args.windows(2)
        .find(|w| w[0] == "--out")
        .map(|w| w[1].clone())
}
