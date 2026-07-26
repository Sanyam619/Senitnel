use std::path::Path;

fn read_kv(path: &Path, key: &str) -> Option<String> {
    let raw = std::fs::read_to_string(path).ok()?;
    for line in raw.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((k, v)) = line.split_once('=') else {
            continue;
        };
        if k.trim() != key {
            continue;
        }
        let rest = v.trim().trim_matches('"');
        if !rest.is_empty() {
            return Some(rest.to_string());
        }
    }
    None
}

fn read_kv_int(path: &Path, key: &str) -> Option<i64> {
    read_kv(path, key)?.parse().ok()
}

fn latest_hold_token(path: &Path) -> Option<String> {
    let raw = std::fs::read_to_string(path).ok()?;
    let mut token = None;
    for line in raw.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if !line.contains("\"event\":\"hold\"") && !line.contains("\"event\": \"hold\"") {
            continue;
        }
        if let Some(idx) = line.find("\"token\"") {
            let rest = &line[idx + 7..];
            if let Some(colon) = rest.find(':') {
                let v = rest[colon + 1..].trim();
                let v = v.trim_start_matches('"');
                let end = v.find('"').unwrap_or(0);
                if end > 0 {
                    token = Some(v[..end].to_string());
                }
            }
        }
    }
    token
}

fn gate_ok() -> bool {
    let cut = Path::new("/app/ops/nx/cut_n.toml");
    let cutover = read_kv(cut, "cutover").unwrap_or_else(|| "pending".into());
    if cutover != "sealed" {
        return false;
    }
    let epoch = read_kv_int(cut, "epoch").unwrap_or(0);
    let floor = read_kv_int(cut, "epoch_floor").unwrap_or(0);
    if epoch < floor {
        return false;
    }
    let hold = read_kv(cut, "hold_token").unwrap_or_default();
    let want = latest_hold_token(Path::new("/app/data/fixtures/desk_journal.jsonl")).unwrap_or_default();
    !hold.is_empty() && !want.is_empty() && hold == want
}

fn copy_file(src: &Path, dst: &Path) {
    if let Ok(body) = std::fs::read(src) {
        let _ = std::fs::create_dir_all(dst.parent().unwrap_or(Path::new("/")));
        let _ = std::fs::write(dst, body);
    }
}

fn copy_if_present(src: &Path, dst: &Path) {
    if src.is_file() {
        copy_file(src, dst);
    }
}

fn rematerialize_all() {
    copy_file(
        Path::new("/app/link/lane_seed.toml"),
        Path::new("/app/config/lane.d/50-draft.toml"),
    );
    copy_file(
        Path::new("/app/link/strand_seed.toml"),
        Path::new("/app/config/profiles/craft.toml"),
    );
    copy_file(
        Path::new("/app/link/fleet_seed.toml"),
        Path::new("/app/config/profiles/fleet.toml"),
    );
    let _ = std::fs::write(Path::new("/app/ops/nx/pref_a.toml"), "prefer = \"archive\"\n");
    let _ = std::fs::write(Path::new("/app/ops/nx/fold_p.toml"), "overlay = \"draft\"\n");
    let _ = std::fs::write(
        Path::new("/app/ops/nx/rel_mask.toml"),
        "strip_b_on_release = true\n",
    );
}

fn promote_nx_live() {
    copy_if_present(
        Path::new("/app/ops/nx/draft_q.toml"),
        Path::new("/app/config/lane.d/50-draft.toml"),
    );
    copy_if_present(
        Path::new("/app/ops/nx/strand_q.toml"),
        Path::new("/app/config/profiles/craft.toml"),
    );
    copy_if_present(
        Path::new("/app/ops/nx/width_q.toml"),
        Path::new("/app/config/profiles/fleet.toml"),
    );
}

fn sync_graph() {
    if gate_ok() {
        promote_nx_live();
    } else {
        rematerialize_all();
    }
}

fn knit_epoch(live: String) -> String {
    sync_graph();
    let prefer = read_kv(Path::new("/app/ops/nx/pref_a.toml"), "prefer")
        .unwrap_or_else(|| "archive".into());
    if prefer == "archive" {
        if let Some(w) = read_kv(Path::new("/app/link/legacy.toml"), "archive_epoch") {
            return w;
        }
        return "3".into();
    }
    live
}

fn knit_members(live: String) -> String {
    sync_graph();
    let prefer = read_kv(Path::new("/app/ops/nx/pref_a.toml"), "prefer")
        .unwrap_or_else(|| "archive".into());
    if prefer == "archive" {
        if let Some(w) = read_kv(Path::new("/app/link/legacy.toml"), "archive_members") {
            return w;
        }
        return "4".into();
    }
    live
}

fn main() {
    let a = std::env::var("STRAND_A").unwrap_or_else(|_| "0".into());
    let mut b = std::env::var("STRAND_B").unwrap_or_else(|_| "0".into());
    let e_live = std::env::var("BITCODE_EPOCH").unwrap_or_else(|_| "3".into());
    let m_live = std::env::var("ARCHIVE_MEMBERS").unwrap_or_else(|_| "4".into());
    let epoch = knit_epoch(e_live);
    let members = knit_members(m_live);
    let release = std::env::var("CELL_RELEASE").unwrap_or_else(|_| "0".into()) == "1";
    let strip_b = read_kv(Path::new("/app/ops/nx/rel_mask.toml"), "strip_b_on_release")
        .unwrap_or_else(|| "false".into())
        == "true";
    if release && strip_b {
        b = "0".into();
    }
    println!("cargo:rerun-if-env-changed=STRAND_A");
    println!("cargo:rerun-if-env-changed=STRAND_B");
    println!("cargo:rerun-if-env-changed=BITCODE_EPOCH");
    println!("cargo:rerun-if-env-changed=ARCHIVE_MEMBERS");
    println!("cargo:rerun-if-env-changed=CELL_RELEASE");
    println!("cargo:rerun-if-changed=/app/link/legacy.toml");
    println!("cargo:rerun-if-changed=/app/link/lane_seed.toml");
    println!("cargo:rerun-if-changed=/app/link/strand_seed.toml");
    println!("cargo:rerun-if-changed=/app/link/fleet_seed.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/pref_a.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/cut_n.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/fold_p.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/rel_mask.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/strand_q.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/width_q.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/draft_q.toml");
    println!("cargo:rerun-if-changed=/app/data/fixtures/desk_journal.jsonl");
    println!("cargo:rustc-check-cfg=cfg(strand_a)");
    println!("cargo:rustc-check-cfg=cfg(strand_b)");
    if a == "1" {
        println!("cargo:rustc-cfg=strand_a");
    }
    if b == "1" {
        println!("cargo:rustc-cfg=strand_b");
    }
    println!("cargo:rustc-env=BITCODE_EPOCH={}", epoch);
    println!("cargo:rustc-env=ARCHIVE_MEMBERS={}", members);
}
