#!/usr/bin/env bash
set -euo pipefail

# Fix 0: Core — lane+strand frame material + rotate-mix helpers
cat > /app/core/src/lib.rs << 'EOF'
use std::fs;
use std::path::Path;

pub const DATA_ROOT: &str = "/app/data";
pub const OPS_ROOT: &str = "/app/ops";
pub const CONFIG_ROOT: &str = "/app/config";
pub const CREDENTIALS_DIR: &str = "/app/data/credentials";
pub const SEGMENTS_DIR: &str = "/app/data/signed_segments";

fn rotl8(x: u8, n: u32) -> u8 {
    let n = n % 8;
    x.rotate_left(n)
}

pub fn load_strand() -> u8 {
    let path = Path::new(OPS_ROOT).join("trust_policy.toml");
    let text = fs::read_to_string(&path).unwrap_or_default();
    for line in text.lines() {
        let t = line.trim();
        if let Some(rest) = t.strip_prefix("strand") {
            if let Some(v) = rest.split('=').nth(1) {
                let raw = v.trim().trim_matches('"');
                if let Ok(n) = raw.parse::<u8>() {
                    return n;
                }
                if let Some(hex) = raw.strip_prefix("0x").or_else(|| raw.strip_prefix("0X")) {
                    if let Ok(n) = u8::from_str_radix(hex, 16) {
                        return n;
                    }
                }
            }
        }
    }
    0
}

pub fn derive_frame_key(seed: &[u8], epoch: u16, lane: u8, strand: u8) -> Vec<u8> {
    let epoch_byte = (epoch & 0xFF) as u8;
    seed.iter()
        .enumerate()
        .map(|(i, b)| {
            let mix = rotl8(epoch_byte, ((i % 5) + 1) as u32);
            let stride = (5u8.wrapping_mul(i as u8)).wrapping_add(1);
            b ^ mix ^ stride ^ strand ^ lane
        })
        .collect()
}

pub fn derive_epoch_key(seed: &[u8], epoch: u16) -> Vec<u8> {
    derive_frame_key(seed, epoch, 0, load_strand())
}
EOF

# Fix 1: Trust chain resolution — match policy class to manifest class
cat > /app/vfy/src/fold_a.rs << 'EOF'
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub struct Policy {
    pub authority_class: String,
    pub verification: String,
    pub replay_protection: String,
    pub strand: u8,
}

pub struct Manifest {
    pub path: String,
    pub class: String,
}

pub fn load_policy() -> Policy {
    let path = Path::new(lattice_core::OPS_ROOT).join("trust_policy.toml");
    let text = fs::read_to_string(&path).unwrap_or_default();
    let authority_class = extract_toml_value(&text, "authority")
        .unwrap_or_else(|| "surface".to_string());
    let verification = extract_toml_value(&text, "verification")
        .unwrap_or_else(|| "plain".to_string());
    let replay_protection = extract_toml_value(&text, "replay_protection")
        .unwrap_or_else(|| "none".to_string());
    let strand = lattice_core::load_strand();
    Policy {
        authority_class,
        verification,
        replay_protection,
        strand,
    }
}

pub fn resolve_manifest(policy: &Policy) -> Manifest {
    let dir = Path::new(lattice_core::DATA_ROOT).join("manifests");
    let Ok(entries) = fs::read_dir(&dir) else {
        return fallback_manifest();
    };
    let mut paths: Vec<_> = entries.filter_map(|e| e.ok().map(|e| e.path())).collect();
    paths.sort();
    for path in &paths {
        let Ok(text) = fs::read_to_string(path) else { continue };
        if let Some(first_line) = text.lines().find(|l| !l.trim().is_empty()) {
            if let Some(class) = extract_json_str(first_line, "\"class\":") {
                if class == policy.authority_class {
                    return Manifest {
                        path: path.to_string_lossy().into_owned(),
                        class,
                    };
                }
            }
        }
    }
    fallback_manifest()
}

fn fallback_manifest() -> Manifest {
    Manifest {
        path: format!("{}/manifests/tier_leaf.jsonl", lattice_core::DATA_ROOT),
        class: "surface".to_string(),
    }
}

pub fn load_watermarks(manifest: &Manifest) -> HashMap<u16, u64> {
    let Ok(text) = fs::read_to_string(&manifest.path) else {
        return HashMap::new();
    };
    let mut map = HashMap::new();
    for line in text.lines() {
        if line.trim().is_empty() { continue; }
        let epoch = extract_json_u16(line, "\"epoch\":").unwrap_or(0);
        let mark = extract_json_u64(line, "\"watermark\":").unwrap_or(0);
        map.insert(epoch, mark);
    }
    map
}

pub fn load_nonces(manifest: &Manifest) -> HashMap<u16, Vec<u8>> {
    // Store raw manifest seeds; frame material is derived per lane at decode time.
    let Ok(text) = fs::read_to_string(&manifest.path) else {
        return HashMap::new();
    };
    let mut map = HashMap::new();
    for line in text.lines() {
        if line.trim().is_empty() { continue; }
        let epoch = extract_json_u16(line, "\"epoch\":").unwrap_or(0);
        let seed_hex = extract_json_str(line, "\"seed\":")
            .or_else(|| extract_json_str(line, "\"nonce\":"))
            .unwrap_or_default();
        let seed_bytes = hex_decode(&seed_hex);
        map.insert(epoch, seed_bytes);
    }
    map
}

fn hex_decode(hex: &str) -> Vec<u8> {
    let mut out = Vec::new();
    let mut chars = hex.chars();
    while let (Some(a), Some(b)) = (chars.next(), chars.next()) {
        if let (Some(hi), Some(lo)) = (a.to_digit(16), b.to_digit(16)) {
            out.push((hi * 16 + lo) as u8);
        }
    }
    out
}

fn extract_toml_value(text: &str, key: &str) -> Option<String> {
    for line in text.lines() {
        let t = line.trim();
        if let Some(rest) = t.strip_prefix(key) {
            if let Some(v) = rest.split('=').nth(1) {
                return Some(v.trim().trim_matches('"').to_string());
            }
        }
    }
    None
}

fn extract_json_str(line: &str, key: &str) -> Option<String> {
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let start = rest.find('"')? + 1;
    let end = start + rest[start..].find('"')?;
    Some(rest[start..end].to_string())
}

fn extract_json_u16(line: &str, key: &str) -> Option<u16> {
    extract_json_u64(line, key).map(|v| v as u16)
}

fn extract_json_u64(line: &str, key: &str) -> Option<u64> {
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let digits: String = rest
        .chars()
        .skip_while(|c| !c.is_ascii_digit())
        .take_while(|c| c.is_ascii_digit())
        .collect();
    digits.parse().ok()
}
EOF

# Fix 2: Segment decode — keyed integrity with derived nonces
cat > /app/vfy/src/sieve_b.rs << 'EOF'
use std::collections::HashMap;

use crate::emit_c::QuarantineEntry;
use crate::skim_fold::Frame;

pub fn decode_wal_with_quarantine(
    raw: &[u8],
    seeds: &HashMap<u16, Vec<u8>>,
    strand: u8,
) -> (Vec<Frame>, Vec<QuarantineEntry>) {
    let lane_names: HashMap<u8, &str> = [
        (1, "mqtt"),
        (2, "lora"),
        (3, "uart"),
        (4, "canbus"),
        (5, "zigbee"),
    ]
    .into_iter()
    .collect();

    let mut accepted = Vec::new();
    let mut rejected = Vec::new();
    let mut i = 0usize;

    while i + 6 <= raw.len() {
        if raw[i] != 0xA5 {
            i += 1;
            continue;
        }
        let lane_id = raw[i + 1];
        let epoch = u16::from_be_bytes([raw[i + 2], raw[i + 3]]);
        let plen = u16::from_be_bytes([raw[i + 4], raw[i + 5]]) as usize;
        let start = i + 6;
        let end = start + plen;
        if end + 1 > raw.len() {
            break;
        }
        let payload = &raw[start..end];
        let stored_integrity = raw[end];

        let text = String::from_utf8_lossy(payload);
        let ts = parse_ts(&text).unwrap_or(0);
        let hold = text.contains("hold=1");
        let lane_name = lane_names.get(&lane_id).unwrap_or(&"unknown");

        let integrity_ok = if let Some(seed) = seeds.get(&epoch) {
            if seed.is_empty() {
                true
            } else {
                let material = lattice_core::derive_frame_key(seed, epoch, lane_id, strand);
                keyed_integrity(payload, &material) == stored_integrity
            }
        } else {
            true
        };

        if integrity_ok {
            accepted.push(Frame {
                epoch,
                lane: lane_name.to_string(),
                ts,
                hold,
                from_wal: true,
            });
        } else {
            rejected.push(QuarantineEntry {
                epoch,
                lane: lane_name.to_string(),
                ts,
                reason: "integrity_failure".to_string(),
            });
        }

        i = end + 1;
    }
    (accepted, rejected)
}

fn keyed_integrity(payload: &[u8], nonce: &[u8]) -> u8 {
    let mut total: u8 = 0;
    for (i, &b) in payload.iter().enumerate() {
        total = total.wrapping_add(b ^ nonce[i % nonce.len()]);
    }
    total
}

fn parse_ts(text: &str) -> Option<u64> {
    let i = text.find("ts=")?;
    let rest = &text[i + 3..];
    let digits: String = rest.chars().take_while(|c| c.is_ascii_digit()).collect();
    digits.parse().ok()
}
EOF

# Fix 3: Main — add replay detection between WAL decode and watermark filter
cat > /app/vfy/src/main.rs << 'EOF'
mod sieve_b;
mod fold_a;
mod skim_sieve;
mod skim_fold;
mod emit_c;

use std::collections::HashMap;
use std::fs;
use std::path::Path;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() >= 2 && args[1] == "attest" {
        let out = parse_out(&args).unwrap_or_else(|| "/output/plugin-ledger.json".to_string());
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

    let mut all_frames: Vec<skim_fold::Frame> = Vec::new();
    let mut quarantine: Vec<emit_c::QuarantineEntry> = Vec::new();

    let cred_dir = Path::new(lattice_core::CREDENTIALS_DIR);
    for lane_name in &["mqtt", "lora", "uart", "canbus", "zigbee"] {
        let path = cred_dir.join(format!("{}.jsonl", lane_name));
        if path.exists() {
            all_frames.extend(skim_fold::load_jsonl_lane(&path, lane_name));
        }
    }

    let mut wal_frames: Vec<skim_fold::Frame> = Vec::new();
    let wal_dir = Path::new(lattice_core::SEGMENTS_DIR);
    if let Ok(entries) = fs::read_dir(&wal_dir) {
        let mut paths: Vec<_> = entries
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.extension().map_or(false, |ext| ext == "bin"))
            .collect();
        paths.sort();
        for path in paths {
            let Ok(raw) = fs::read(&path) else { continue };
            let (accepted, rejected) =
                sieve_b::decode_wal_with_quarantine(&raw, &nonces, policy.strand);
            wal_frames.extend(accepted);
            quarantine.extend(rejected);
        }
    }

    if policy.replay_protection == "monotonic" {
        let mut max_ts: HashMap<(u16, String), u64> = HashMap::new();
        let mut replay_filtered = Vec::new();
        for f in wal_frames {
            let key = (f.epoch, f.lane.clone());
            let prev = max_ts.get(&key).copied().unwrap_or(0);
            if prev > 0 && f.ts <= prev {
                quarantine.push(emit_c::QuarantineEntry {
                    epoch: f.epoch,
                    lane: f.lane.clone(),
                    ts: f.ts,
                    reason: "replay".to_string(),
                });
            } else {
                max_ts.insert(key, f.ts);
                replay_filtered.push(f);
            }
        }
        all_frames.extend(replay_filtered);
    } else {
        all_frames.extend(wal_frames);
    }

    let filtered: Vec<skim_fold::Frame> = all_frames
        .into_iter()
        .filter(|f| {
            let mark = marks.get(&f.epoch).copied().unwrap_or(0);
            f.ts <= mark
        })
        .collect();

    let classified = skim_sieve::classify(&filtered, &revocations);
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

    let roster = skim_fold::evaluate(&classified, &profiles, &matrix);

    if let Err(e) = emit_c::write_roster(out, &roster) {
        eprintln!("emit failed: {e}");
        std::process::exit(1);
    }

    let quarantine_path = out.replace("plugin-ledger", "quarantine");
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

fn parse_out(args: &[String]) -> Option<String> {
    args.windows(2)
        .find(|w| w[0] == "--out")
        .map(|w| w[1].clone())
}
EOF

# Fix 4: Emit — remove deduplication that drops multiple entries per stream
cat > /app/vfy/src/emit_c.rs << 'EOF'
use std::fs;
use std::io;
use std::path::Path;

use crate::skim_fold::Roster;

pub struct QuarantineEntry {
    pub epoch: u16,
    pub lane: String,
    pub ts: u64,
    pub reason: String,
}

pub fn write_roster(path: &str, roster: &Roster) -> io::Result<()> {
    if path.trim().is_empty() {
        return Err(io::Error::new(io::ErrorKind::InvalidInput, "empty path"));
    }
    if let Some(parent) = Path::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)?;
        }
    }
    let mut body = String::from("{\n  \"version\": 1,\n  \"backends\": [\n");
    for (i, (name, status)) in roster.backends.iter().enumerate() {
        if i > 0 {
            body.push_str(",\n");
        }
        body.push_str(&format!(
            "    {{\"name\": \"{}\", \"status\": \"{}\"}}",
            escape(name),
            escape(status)
        ));
    }
    body.push_str("\n  ],\n  \"epochs\": [\n");
    for (i, (id, profile, accepted)) in roster.epochs.iter().enumerate() {
        if i > 0 {
            body.push_str(",\n");
        }
        body.push_str(&format!(
            "    {{\"id\": {}, \"profile\": \"{}\", \"accepted\": {}}}",
            id,
            escape(profile),
            accepted
        ));
    }
    body.push_str("\n  ]\n}\n");
    fs::write(path, body)
}

pub fn write_quarantine(path: &str, entries: &[QuarantineEntry]) -> io::Result<()> {
    if path.trim().is_empty() {
        return Err(io::Error::new(io::ErrorKind::InvalidInput, "empty path"));
    }
    if let Some(parent) = Path::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)?;
        }
    }
    let mut body = String::from("{\n  \"version\": 1,\n  \"rejected\": [\n");
    for (i, e) in entries.iter().enumerate() {
        if i > 0 {
            body.push_str(",\n");
        }
        body.push_str(&format!(
            "    {{\"epoch\": {}, \"lane\": \"{}\", \"ts\": {}, \"reason\": \"{}\"}}",
            e.epoch,
            escape(&e.lane),
            e.ts,
            escape(&e.reason)
        ));
    }
    body.push_str("\n  ]\n}\n");
    fs::write(path, body)
}

fn escape(raw: &str) -> String {
    raw.replace('\\', "\\\\").replace('"', "\\\"")
}
EOF

# Fix 5: Co-presence — Held counts for required-together presence; accepted excludes Held/Revoked
cat > /app/vfy/src/skim_fold.rs << 'EOF'
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::Path;

use crate::skim_sieve::{ClassifiedFrame, FrameStatus};

#[derive(Clone)]
pub struct Frame {
    pub epoch: u16,
    pub lane: String,
    pub ts: u64,
    pub hold: bool,
    pub from_wal: bool,
}

pub struct Profile {
    pub label: String,
    pub epochs: Vec<u16>,
}

pub struct MatrixEntry {
    pub lanes: Vec<String>,
    pub mode: String,
}

pub struct Roster {
    pub backends: Vec<(String, String)>,
    pub epochs: Vec<(u16, String, u32)>,
}

pub fn load_profiles() -> HashMap<String, Profile> {
    let dir = Path::new(lattice_core::CONFIG_ROOT).join("profiles");
    let mut map = HashMap::new();
    let Ok(entries) = fs::read_dir(&dir) else {
        return map;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().map_or(true, |e| e != "toml") {
            continue;
        }
        let Ok(text) = fs::read_to_string(&path) else { continue };
        let label = extract_toml_str(&text, "label").unwrap_or_default();
        let epochs = extract_toml_array_u16(&text, "epochs");
        if !label.is_empty() {
            map.insert(label.clone(), Profile { label, epochs });
        }
    }
    map
}

pub fn load_matrix() -> HashMap<String, MatrixEntry> {
    let path = Path::new(lattice_core::OPS_ROOT).join("matrix.toml");
    let Ok(text) = fs::read_to_string(&path) else {
        return HashMap::new();
    };
    let mut map = HashMap::new();
    let mut current_section: Option<String> = None;
    let mut current_lanes: Vec<String> = Vec::new();
    let mut current_mode = String::new();

    for line in text.lines() {
        let t = line.trim();
        if t.starts_with('[') && t.ends_with(']') {
            if let Some(section) = current_section.take() {
                if !current_lanes.is_empty() {
                    map.insert(
                        section,
                        MatrixEntry {
                            lanes: current_lanes.clone(),
                            mode: current_mode.clone(),
                        },
                    );
                }
            }
            current_section = Some(t[1..t.len() - 1].to_string());
            current_lanes.clear();
            current_mode.clear();
        } else if let Some(rest) = t.strip_prefix("lanes") {
            if let Some(arr) = rest.split('=').nth(1) {
                current_lanes = parse_string_array(arr);
            }
        } else if let Some(rest) = t.strip_prefix("mode") {
            if let Some(v) = rest.split('=').nth(1) {
                current_mode = v.trim().trim_matches('"').to_string();
            }
        }
    }
    if let Some(section) = current_section {
        if !current_lanes.is_empty() {
            map.insert(
                section,
                MatrixEntry {
                    lanes: current_lanes,
                    mode: current_mode,
                },
            );
        }
    }
    map
}

pub fn load_jsonl_lane(path: &Path, lane_name: &str) -> Vec<Frame> {
    let Ok(text) = fs::read_to_string(path) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for line in text.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let epoch = extract_json_u16(line, "\"epoch\":").unwrap_or(0);
        let ts = extract_json_u64(line, "\"ts\":").unwrap_or(0);
        let hold = line.contains("\"hold\":true");
        out.push(Frame {
            epoch,
            lane: lane_name.to_string(),
            ts,
            hold,
            from_wal: false,
        });
    }
    out
}

pub fn evaluate(
    frames: &[ClassifiedFrame],
    profiles: &HashMap<String, Profile>,
    matrix: &HashMap<String, MatrixEntry>,
) -> Roster {
    let all_lanes = ["mqtt", "lora", "uart", "canbus", "zigbee"];
    let mut active_backends: HashSet<String> = HashSet::new();
    let mut epochs: Vec<(u16, String, u32)> = Vec::new();

    for (prof_name, profile) in profiles {
        let entry = match matrix.get(prof_name) {
            Some(e) => e,
            None => continue,
        };

        for &epoch in &profile.epochs {
            let epoch_frames: Vec<&ClassifiedFrame> = frames
                .iter()
                .filter(|f| f.epoch == epoch && entry.lanes.contains(&f.lane))
                .collect();

            let publish = match entry.mode.as_str() {
                "required-together" => entry.lanes.iter().all(|lane| {
                    epoch_frames.iter().any(|f| {
                        &f.lane == lane
                            && (f.status == FrameStatus::Active || f.status == FrameStatus::Held)
                    })
                }),
                _ => !epoch_frames.is_empty(),
            };

            if publish {
                let count = epoch_frames
                    .iter()
                    .filter(|f| f.status != FrameStatus::Revoked && f.status != FrameStatus::Held)
                    .count() as u32;

                if count > 0 {
                    epochs.push((epoch, prof_name.clone(), count));
                }

                for f in &epoch_frames {
                    if f.status == FrameStatus::Active {
                        active_backends.insert(f.lane.clone());
                    }
                }
            }
        }
    }

    epochs.sort_by_key(|(e, _, _)| *e);

    let backends: Vec<(String, String)> = all_lanes
        .iter()
        .map(|&l| {
            let status = if active_backends.contains(l) {
                "active"
            } else {
                "inactive"
            };
            (l.to_string(), status.to_string())
        })
        .collect();

    Roster { backends, epochs }
}

fn extract_toml_str(text: &str, key: &str) -> Option<String> {
    for line in text.lines() {
        let t = line.trim();
        if let Some(rest) = t.strip_prefix(key) {
            if let Some(v) = rest.split('=').nth(1) {
                let trimmed = v.trim().trim_matches('"');
                return Some(trimmed.to_string());
            }
        }
    }
    None
}

fn extract_toml_array_u16(text: &str, key: &str) -> Vec<u16> {
    for line in text.lines() {
        let t = line.trim();
        if let Some(rest) = t.strip_prefix(key) {
            let bracket = rest.find('[').and_then(|i| rest[i + 1..].find(']').map(|j| (i, j)));
            if let Some((i, j)) = bracket {
                let inner = &rest[i + 1..i + 1 + j];
                return inner
                    .split(',')
                    .filter_map(|s| s.trim().parse::<u16>().ok())
                    .collect();
            }
        }
    }
    Vec::new()
}

fn parse_string_array(text: &str) -> Vec<String> {
    let trimmed = text.trim();
    let inner = trimmed
        .strip_prefix('[')
        .and_then(|s| s.strip_suffix(']'))
        .unwrap_or(trimmed);
    inner
        .split(',')
        .map(|s| s.trim().trim_matches('"').to_string())
        .filter(|s| !s.is_empty())
        .collect()
}

fn extract_json_u16(line: &str, key: &str) -> Option<u16> {
    extract_json_u64(line, key).map(|v| v as u16)
}

fn extract_json_u64(line: &str, key: &str) -> Option<u64> {
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let digits: String = rest
        .chars()
        .skip_while(|c| !c.is_ascii_digit())
        .take_while(|c| c.is_ascii_digit())
        .collect();
    digits.parse().ok()
}
EOF

# Build and run
cd /app
cargo build -p trusteval --release
/app/target/release/trusteval attest --out /output/plugin-ledger.json
