use std::{collections::BTreeSet, fs, path::Path};

use crate::{cfg, digest, io, state::Runtime};

pub fn status(root: &Path) -> Result<(), String> {
    let rt = Runtime::load(root)?;
    println!(
        "{{\"active_batch\":{},\"ceiling_batch\":{},\"sensor_seq\":{}}}",
        rt.active_batch, rt.ceiling_batch, rt.sensor_seq
    );
    Ok(())
}

pub fn bind(root: &Path, cfg_dir: &Path) -> Result<(), String> {
    let mut rt = Runtime::load(root)?;
    if !cfg::boolv(cfg_dir, "a3.toml", "bind_ready")? {
        return Err("bind refused: bind_ready is false".into());
    }
    let floor = cfg::u64v(cfg_dir, "a3.toml", "batch_floor")?;
    let pin = cfg::u64v(cfg_dir, "a3.toml", "ledger_pin")?;
    let cursor = cfg::u64v(cfg_dir, "a3.toml", "cold_cursor")?;
    if floor != pin || pin != cursor {
        return Err("bind refused: batch_floor, ledger_pin, and cold_cursor disagree".into());
    }
    rt.active_batch = floor;
    rt.hold_lots.clear();
    rt.save(root)?;
    println!("bound batch {floor}");
    Ok(())
}

pub fn sweep(root: &Path, cfg_dir: &Path) -> Result<(), String> {
    let mut rt = Runtime::load(root)?;
    let enabled = cfg::boolv(cfg_dir, "m5.toml", "hold_enabled")?;
    let window = cfg::u64v(cfg_dir, "c8.toml", "sensor_ceiling")?;
    let cutoff_cfg = cfg::u64v(cfg_dir, "c8.toml", "sensor_cutoff")?;
    let events = io::sensors(root)?;
    let mut lots = BTreeSet::new();
    if enabled {
        for ev in &events {
            if ev.seq <= window && ev.status == "hold" {
                lots.insert(ev.lot.clone());
            }
        }
    }
    rt.sensor_seq = cutoff_cfg;
    rt.hold_lots = lots.into_iter().collect();
    rt.save(root)?;
    println!("swept through {cutoff_cfg}");
    Ok(())
}

pub fn seal(root: &Path, cfg_dir: &Path, lane_path: &Path) -> Result<(), String> {
    let lane = lane_path.to_string_lossy().to_string();
    let rt = Runtime::load(root)?;
    let ceiling = cfg::u64v(cfg_dir, "c8.toml", "sensor_ceiling")?;
    let max_seq = io::sensors(root)?
        .into_iter()
        .map(|e| e.seq)
        .max()
        .unwrap_or(0);
    if ceiling != max_seq {
        return Err(format!(
            "seal refused: sensor_ceiling {ceiling} drifts from spool high-water {max_seq}"
        ));
    }
    let mode = cfg::strv(cfg_dir, "m5.toml", "quarantine_mode")?;
    let respect_holds = mode == "active";
    let mut lots = Vec::new();
    for s in io::shipments(root)? {
        if s.lane != lane || s.batch > rt.active_batch {
            continue;
        }
        if respect_holds && rt.hold_lots.contains(&s.lot) {
            continue;
        }
        lots.push(s.lot);
    }
    lots.sort();
    lots.dedup();
    let dg = digest::digest(&lots);
    let list = lots
        .iter()
        .map(|v| format!("\"{v}\""))
        .collect::<Vec<_>>()
        .join(", ");
    let body = format!(
        "{{\n  \"lane\": \"{}\",\n  \"bound_batch\": {},\n  \"lots\": [{}],\n  \"digest\": \"{}\"\n}}\n",
        lane, rt.active_batch, list, dg
    );
    fs::write(root.join("sidecars").join(format!("{lane}.idx")), body)
        .map_err(|e| format!("write sidecar: {e}"))?;
    println!("sealed {lane} {}", lots.len());
    Ok(())
}
