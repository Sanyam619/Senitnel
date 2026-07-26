use crate::{extract_string_after, parse_slots_block, plugin_block, read_file, Row};
use std::collections::HashMap;

/// Emits layout rows for sievectl from the rust lane pin file.
pub fn sieve_b(a: &str, b: &str) -> Result<Vec<Row>, String> {
    let reg = if a.is_empty() {
        "/app/data/registry"
    } else {
        a
    };
    let pin_path = if b.is_empty() {
        "/app/rsx/pins.toml".to_string()
    } else {
        b.to_string()
    };

    let pin = read_pin_map(&pin_path)?;
    let mut plugin_key = pin
        .get("plugin_key")
        .cloned()
        .unwrap_or_default();
    if pin.get("skim_prefer").map(|s| s.as_str()) == Some("true") {
        if let Some(sk) = pin.get("skim_plugin") {
            plugin_key = sk.clone();
        }
    }
    if pin.get("json_owner").map(|s| s.as_str()) == Some("archive") {
        if let Some(ak) = pin.get("archive_plugin") {
            plugin_key = ak.clone();
        }
    }

    let meta = read_file(&format!("{}/plugin_meta.json", reg))?;
    let live = extract_string_after(&meta, "live_key").unwrap_or_else(|| "pg-core@0.9.2".to_string());
    let cand = if plugin_key.is_empty() {
        pin.get("fallback_plugin").cloned().unwrap_or(live)
    } else {
        plugin_key
    };
    let block = plugin_block(&meta, &cand)?;
    parse_slots_block(&block)
}

fn read_pin_map(path: &str) -> Result<HashMap<String, String>, String> {
    let raw = read_file(path)?;
    let mut out = HashMap::new();
    for line in raw.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((k, v)) = line.split_once('=') else {
            continue;
        };
        out.insert(
            k.trim().to_string(),
            v.trim().trim_matches('"').to_string(),
        );
    }
    Ok(out)
}
