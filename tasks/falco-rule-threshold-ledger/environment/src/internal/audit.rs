use crate::internal::cfg;
use crate::internal::replay;
use std::fs;

pub fn run_pack(pack_path: &str, out_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let pack: serde_json::Value = serde_json::from_str(&fs::read_to_string(pack_path)?)?;
    let batches: Vec<String> = pack["batches"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|v| v.as_str().map(|s| s.to_string()))
        .collect();
    let rules = cfg::load_rules("/app/data/rules/catalog.json")?;
    let floor = cfg::load_floor("/app/config/priority_floor.toml")?;
    let window_sec = cfg::load_window("/app/config/rate_policy.toml")?;
    let mut audits = Vec::new();
    for bid in &batches {
        let path = format!("/app/data/batches/{bid}.jsonl");
        let events = crate::internal::tape::read_batch(&path)?;
        audits.push(replay::replay_batch(bid, &events, &rules, floor, window_sec));
    }
    let pack_ok = replay::guard_ok(&audits);
    let report = serde_json::json!({
        "audits": audits,
        "summary": {"pack_ok": pack_ok, "audited_count": batches.len()},
    });
    fs::write(out_path, format!("{}\n", serde_json::to_string(&report)?))?;
    Ok(())
}
