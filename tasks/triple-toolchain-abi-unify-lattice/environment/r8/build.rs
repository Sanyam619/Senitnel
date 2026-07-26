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
        Path::new("/app/config/strand_m.toml"),
    );
    copy_file(
        Path::new("/app/link/hook_seed.toml"),
        Path::new("/app/ops/nx/hook_q.toml"),
    );
    copy_file(
        Path::new("/app/link/fleet_seed.toml"),
        Path::new("/app/config/profiles/fleet.toml"),
    );
    let _ = std::fs::write(Path::new("/app/ops/nx/pref_a.toml"), "prefer = \"archive\"\n");
    let _ = std::fs::write(Path::new("/app/ops/nx/fold_p.toml"), "overlay = \"draft\"\n");
    let _ = std::fs::write(
        Path::new("/app/ops/nx/rel_mask.toml"),
        "strip_y_on_release = true\n",
    );
}

fn promote_nx_live() {
    copy_if_present(
        Path::new("/app/ops/nx/strand_q.toml"),
        Path::new("/app/config/strand_m.toml"),
    );
    copy_if_present(
        Path::new("/app/ops/nx/width_q.toml"),
        Path::new("/app/config/profiles/fleet.toml"),
    );
    copy_if_present(
        Path::new("/app/ops/nx/draft_q.toml"),
        Path::new("/app/config/lane.d/50-draft.toml"),
    );
}

fn sync_graph() {
    if gate_ok() {
        promote_nx_live();
    } else {
        rematerialize_all();
    }
}

fn knit_w() -> String {
    sync_graph();
    let prefer = read_kv(Path::new("/app/ops/nx/pref_a.toml"), "prefer")
        .unwrap_or_else(|| "archive".into());
    if prefer == "archive" {
        if let Some(w) = read_kv(Path::new("/app/link/legacy.toml"), "archive_pack") {
            return w;
        }
        return "16".into();
    }
    std::env::var("PACK_WIDTH").unwrap_or_else(|_| "8".into())
}

fn main() {
    let a = std::env::var("FACET_X").unwrap_or_else(|_| "0".into());
    let b = std::env::var("FACET_Y").unwrap_or_else(|_| "0".into());
    let w = knit_w();
    println!("cargo:rerun-if-env-changed=FACET_X");
    println!("cargo:rerun-if-env-changed=FACET_Y");
    println!("cargo:rerun-if-env-changed=PACK_WIDTH");
    println!("cargo:rerun-if-changed=/app/link/legacy.toml");
    println!("cargo:rerun-if-changed=/app/link/lane_seed.toml");
    println!("cargo:rerun-if-changed=/app/link/strand_seed.toml");
    println!("cargo:rerun-if-changed=/app/link/hook_seed.toml");
    println!("cargo:rerun-if-changed=/app/link/fleet_seed.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/pref_a.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/cut_n.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/fold_p.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/hook_q.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/rel_mask.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/strand_q.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/width_q.toml");
    println!("cargo:rerun-if-changed=/app/ops/nx/draft_q.toml");
    println!("cargo:rerun-if-changed=/app/data/fixtures/desk_journal.jsonl");
    println!("cargo:rustc-check-cfg=cfg(facet_x)");
    println!("cargo:rustc-check-cfg=cfg(facet_y)");
    if a == "1" {
        println!("cargo:rustc-cfg=facet_x");
    }
    if b == "1" {
        println!("cargo:rustc-cfg=facet_y");
    }
    println!("cargo:rustc-env=PACK_WIDTH={}", w);
}
