use crate::types::*;
use std::fs;
use std::path::{Path, PathBuf};

pub fn load_state(base: &Path) -> StateNow {
    let raw = fs::read_to_string(base.join("state").join("now.json")).expect("read now.json");
    serde_json::from_str(&raw).expect("parse now.json")
}

pub fn load_ceremony(base: &Path) -> Ledger {
    let raw = fs::read_to_string(base.join("ceremony").join("ledger.json")).expect("read ledger");
    let mut led: Ledger = serde_json::from_str(&raw).expect("parse ledger");
    led.rotations.sort_by_key(|r| r.effective_epoch);
    led
}

pub fn load_cosigners(base: &Path) -> CosignerBook {
    let raw =
        fs::read_to_string(base.join("ceremony").join("cosigners.json")).expect("read cosigners");
    serde_json::from_str(&raw).expect("parse cosigners")
}

pub fn load_shards(base: &Path) -> ShardBook {
    let mut book = ShardBook::default();
    let shards_root = base.join("shards");
    let mut shard_dirs: Vec<PathBuf> = fs::read_dir(&shards_root)
        .expect("open shards")
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    shard_dirs.sort();
    for shard_dir in shard_dirs {
        let shard_id = shard_dir
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_string();
        let cp_dir = shard_dir.join("checkpoints");
        let mut checkpoints: Vec<Checkpoint> = Vec::new();
        let mut cp_files: Vec<PathBuf> = fs::read_dir(&cp_dir)
            .expect("open checkpoints")
            .flatten()
            .map(|e| e.path())
            .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
            .collect();
        cp_files.sort();
        for f in cp_files {
            let raw = fs::read_to_string(&f).expect("read checkpoint");
            let cp: Checkpoint = serde_json::from_str(&raw).expect("parse checkpoint");
            checkpoints.push(cp);
        }
        checkpoints.sort_by_key(|c| c.epoch);
        book.by_id.insert(
            shard_id.clone(),
            Shard {
                shard_id,
                checkpoints,
            },
        );
    }
    book
}

pub fn load_event(path: &Path) -> Event {
    let raw = fs::read_to_string(path).expect("read event");
    serde_json::from_str(&raw).expect("parse event")
}

pub fn load_events(base: &Path) -> Vec<Event> {
    let dir = base.join("events");
    let mut paths: Vec<PathBuf> = fs::read_dir(&dir)
        .expect("open events")
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
        .collect();
    paths.sort();
    let mut out = Vec::new();
    for p in paths {
        out.push(load_event(&p));
    }
    out.sort_by(|a, b| a.event_id.cmp(&b.event_id));
    out
}
