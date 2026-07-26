use std::env;
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

fn getenv(k: &str, d: &str) -> String {
    env::var(k).unwrap_or_else(|_| d.to_string())
}

fn read_cap(seal: &Path) -> io::Result<i64> {
    for line in fs::read_to_string(seal)?.lines() {
        let t = line.trim();
        if !t.is_empty() && !t.starts_with('#') {
            return Ok(t.parse().unwrap_or(0));
        }
    }
    Ok(0)
}

fn read_pref_mode(root: &Path) -> String {
    let armed = root.join("meta/pref.armed");
    if let Ok(s) = fs::read_to_string(&armed) {
        let m = s.trim();
        if !m.is_empty() {
            return m.to_string();
        }
    }
    "strict-gt".to_string()
}

fn is_incr(mode: &str, epoch: i64, floor: i64) -> bool {
    if mode == "equality-inclusive" {
        epoch >= floor
    } else {
        epoch > floor
    }
}

fn main() {
    let root = PathBuf::from(getenv("BTRFS_ROOT", "/var/lib/btrfs"));
    let seal = PathBuf::from(getenv("BTRFS_SEAL", "/etc/btrfs/pool.seal"));
    let out_dir = PathBuf::from(getenv("LANE_OUT", "/output/lanes"));
    let report = PathBuf::from(getenv("SEND_REPORT", "/output/send-report.json"));
    let lease_dir = PathBuf::from(getenv("LEASE_DIR", "/var/run/btrfs"));
    let attach = root.join("attach");
    let runtime = root.join("meta/runtime.tsv");
    let seal_arm = root.join("meta/seal_gen.arm");

    let cap = match read_cap(&seal) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("seal: {e}");
            std::process::exit(1);
        }
    };
    let armed_cap = fs::read_to_string(&seal_arm)
        .ok()
        .and_then(|s| s.trim().parse::<i64>().ok())
        .unwrap_or(-1);
    if armed_cap != cap {
        eprintln!("seal gate mismatch arm={armed_cap} seal={cap}");
        std::process::exit(1);
    }

    let intent = fs::read_to_string(root.join("meta/attach.intent"))
        .unwrap_or_default();
    if intent.trim() != "seal" {
        eprintln!("attach intent not sealed: {}", intent.trim());
        std::process::exit(1);
    }

    let mode = read_pref_mode(&root);
    if mode != "equality-inclusive" {
        eprintln!("pref mode not armed: {mode}");
        std::process::exit(1);
    }

    let text = match fs::read_to_string(&runtime) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("runtime: {e}");
            std::process::exit(1);
        }
    };

    let _ = fs::create_dir_all(&out_dir);
    let _ = fs::create_dir_all(&lease_dir);

    let mut json_lanes = String::new();
    let mut first = true;

    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split('\t').collect();
        if parts.len() < 7 {
            continue;
        }
        let order: i64 = parts[0].parse().unwrap_or(0);
        let name = parts[1];
        let parent = parts[2];
        let snap = parts[3];
        let origin = parts[4];
        let epoch: i64 = parts[5].parse().unwrap_or(0);
        let floor: i64 = parts[6].parse().unwrap_or(0);

        let incr = is_incr(&mode, epoch, floor);
        let kind = if incr { "incr" } else { "base" };

        let bytes = if incr {
            let sealed_attach = attach.join(format!("{name}.bin"));
            let snap_path = root.join("snaps/payloads").join(format!("{snap}.bin"));
            if sealed_attach.exists() {
                fs::read(&sealed_attach).unwrap_or_default()
            } else {
                fs::read(&snap_path).unwrap_or_default()
            }
        } else {
            let src = root.join("origins").join(format!("{origin}.bin"));
            fs::read(&src).unwrap_or_default()
        };

        let lane_dir = out_dir.join(name);
        let _ = fs::create_dir_all(&lane_dir);
        if let Err(e) = fs::write(lane_dir.join("stream.bin"), &bytes) {
            eprintln!("write stream: {e}");
            std::process::exit(1);
        }

        let _ = fs::remove_file(lease_dir.join(format!("{name}.part")));

        if !first {
            json_lanes.push(',');
        }
        first = false;
        json_lanes.push_str(&format!(
            "{{\"name\":\"{name}\",\"parent_uuid\":\"{parent}\",\"snap_uuid\":\"{snap}\",\"origin_kind\":\"{kind}\",\"order_index\":{order}}}"
        ));
    }

    let body = format!("{{\"seal_gen\":{cap},\"lanes\":[{json_lanes}]}}\n");
    if let Err(e) = fs::write(&report, body) {
        eprintln!("report: {e}");
        std::process::exit(1);
    }
    let _ = writeln!(io::stdout(), "ok report={}", report.display());
}
