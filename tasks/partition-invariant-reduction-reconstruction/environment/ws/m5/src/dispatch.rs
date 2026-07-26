use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use m3::types::MetricBundle;
use m7::load::read_checkpoint;
use m9::session::run_session;
use m9::topology::read_layout;
use serde::Serialize;

#[derive(Serialize)]
pub struct Row {
    pub layout: String,
    pub scenario: String,
    #[serde(flatten)]
    pub metrics: MetricBundle,
}

pub fn all_layouts(data_root: &Path, out_dir: &Path) -> std::io::Result<()> {
    std::fs::create_dir_all(out_dir)?;
    let ck_dir = data_root.join("checkpoints");
    let layout_dir = data_root.join("layouts");
    let mut rows: Vec<Row> = Vec::new();
    let mut owners: BTreeMap<String, BTreeMap<String, u32>> = BTreeMap::new();

    for entry in std::fs::read_dir(&layout_dir)? {
        let path = entry?.path();
        if path.extension().and_then(|s| s.to_str()) != Some("toml") {
            continue;
        }
        let layout = read_layout(&path)?;
        let mut layout_owners: BTreeMap<String, u32> = BTreeMap::new();
        let last_rank = layout.ranks.saturating_sub(1);
        for seg in &layout.segments {
            if layout.overlap > 0 && seg.rank < last_rank {
                let owner = (seg.rank + 1).min(last_rank);
                layout_owners.insert(seg.hi.to_string(), owner);
            }
        }
        owners.insert(layout.name.clone(), layout_owners);

        for ck_entry in std::fs::read_dir(&ck_dir)? {
            let ck_path = ck_entry?.path();
            if ck_path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let scenario = ck_path.file_stem().unwrap().to_string_lossy().to_string();
            if !scenario.starts_with("tape_") {
                continue;
            }
            let ck = read_checkpoint(&ck_path)?;
            let metrics = run_session(&layout, &ck);
            rows.push(Row {
                layout: layout.name.clone(),
                scenario,
                metrics,
            });
        }
    }

    rows.sort_by(|a, b| (&a.layout, &a.scenario).cmp(&(&b.layout, &b.scenario)));
    let reductions = out_dir.join("reductions.json");
    std::fs::write(&reductions, serde_json::to_string_pretty(&rows)?)?;
    let ownership = out_dir.join("ownership.json");
    std::fs::write(&ownership, serde_json::to_string_pretty(&owners)?)?;
    Ok(())
}

pub fn default_data_root() -> PathBuf {
    PathBuf::from("/app/data")
}
