#!/bin/bash
set -euo pipefail
mkdir -p /output /tmp/diversion-work

# Patch ctl: stop wiping holds on bind; apply holds via sensor_cutoff with latest-status wins.
cat > /app/src/ops.rs <<'EOF'
use std::{collections::BTreeMap, collections::BTreeSet, fs, path::Path};

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
    rt.save(root)?;
    println!("bound batch {floor}");
    Ok(())
}

fn latest_status_by_lot(events: &[io::Sensor], window: u64) -> BTreeMap<String, String> {
    let mut best: BTreeMap<String, (u64, String)> = BTreeMap::new();
    for ev in events {
        if ev.seq > window {
            continue;
        }
        let replace = match best.get(&ev.lot) {
            Some((seq, _)) => ev.seq >= *seq,
            None => true,
        };
        if replace {
            best.insert(ev.lot.clone(), (ev.seq, ev.status.clone()));
        }
    }
    best.into_iter().map(|(lot, (_, st))| (lot, st)).collect()
}

pub fn sweep(root: &Path, cfg_dir: &Path) -> Result<(), String> {
    let mut rt = Runtime::load(root)?;
    let enabled = cfg::boolv(cfg_dir, "m5.toml", "hold_enabled")?;
    let window = cfg::u64v(cfg_dir, "c8.toml", "sensor_cutoff")?;
    let events = io::sensors(root)?;
    let mut lots = BTreeSet::new();
    if enabled {
        for (lot, status) in latest_status_by_lot(&events, window) {
            if status == "hold" {
                lots.insert(lot);
            }
        }
    }
    rt.sensor_seq = window;
    rt.hold_lots = lots.into_iter().collect();
    rt.save(root)?;
    println!("swept through {window}");
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
EOF

(cd /app/src && rustc --edition=2021 main.rs -O -o /app/bin/ctl)

restored_batch=42
hold_seq=713
spool_top=721
cfg=/app/config/l7

sed -i "s/^batch_floor = .*/batch_floor = ${restored_batch}/" "$cfg/a3.toml"
sed -i "s/^ledger_pin = .*/ledger_pin = ${restored_batch}/" "$cfg/a3.toml"
sed -i "s/^cold_cursor = .*/cold_cursor = ${restored_batch}/" "$cfg/a3.toml"
sed -i 's/^bind_ready = .*/bind_ready = true/' "$cfg/a3.toml"

sed -i "s/^sensor_cutoff = .*/sensor_cutoff = ${hold_seq}/" "$cfg/c8.toml"
sed -i "s/^sensor_ceiling = .*/sensor_ceiling = ${spool_top}/" "$cfg/c8.toml"
sed -i "s/^dock_a_cursor = .*/dock_a_cursor = ${spool_top}/" "$cfg/c8.toml"
sed -i "s/^dock_b_cursor = .*/dock_b_cursor = ${spool_top}/" "$cfg/c8.toml"
sed -i "s/^dock_c_cursor = .*/dock_c_cursor = ${spool_top}/" "$cfg/c8.toml"
sed -i 's/^scan_ready = .*/scan_ready = true/' "$cfg/c8.toml"

sed -i 's/^hold_enabled = .*/hold_enabled = true/' "$cfg/m5.toml"
sed -i 's/^quarantine_mode = .*/quarantine_mode = "active"/' "$cfg/m5.toml"
sed -i "s/^hold_gate = .*/hold_gate = ${hold_seq}/" "$cfg/m5.toml"
sed -i 's/^sensor_mode = .*/sensor_mode = "sealed"/' "$cfg/m5.toml"

sed -i "s/^cold_sidecar_batch = .*/cold_sidecar_batch = ${restored_batch}/" "$cfg/r2.toml"
sed -i "s/^ambient_sidecar_batch = .*/ambient_sidecar_batch = ${restored_batch}/" "$cfg/r2.toml"
sed -i 's/^digest_ready = .*/digest_ready = true/' "$cfg/r2.toml"
sed -i 's/^report_ready = .*/report_ready = true/' "$cfg/r2.toml"

/app/bin/ctl bind
/app/bin/ctl sweep
/app/bin/ctl seal --lane cold
/app/bin/ctl seal --lane ambient
/app/bin/ctl report --out /output/diversion-report.json
