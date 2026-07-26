use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct Arms {
    pub precedence: String,
    pub borrow_gate: String,
    pub fragment_order: String,
}

fn scan_kv(text: &str) -> BTreeMap<String, String> {
    let mut m = BTreeMap::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((k, v)) = line.split_once('=') {
            m.insert(k.trim().to_string(), v.trim().to_string());
        }
    }
    m
}

const KEYS: &[&str] = &["precedence_mode", "borrow_gate", "fragment_order"];

pub fn arm_q(_app: &Path) -> Result<Arms, String> {
    let active_text = fs::read_to_string("/etc/fleet/reconcile.conf").map_err(|e| e.to_string())?;
    let std_text =
        fs::read_to_string("/etc/fleet/site_standard.conf").map_err(|e| e.to_string())?;
    let active = scan_kv(&active_text);
    let standard = scan_kv(&std_text);

    let mut matched = true;
    for k in KEYS {
        let a = active.get(*k).map(|s| s.as_str()).unwrap_or("");
        let s = standard.get(*k).map(|s| s.as_str()).unwrap_or("");
        if a != s {
            matched = false;
            break;
        }
    }

    if matched {
        Ok(Arms {
            precedence: active
                .get("precedence_mode")
                .cloned()
                .unwrap_or_else(|| "seal_first".into()),
            borrow_gate: active
                .get("borrow_gate")
                .cloned()
                .unwrap_or_else(|| "live_and_clear".into()),
            fragment_order: active
                .get("fragment_order")
                .cloned()
                .unwrap_or_else(|| "seal_ordinal".into()),
        })
    } else {
        Ok(Arms {
            precedence: active
                .get("precedence_mode")
                .cloned()
                .unwrap_or_else(|| "legacy".into()),
            borrow_gate: active
                .get("borrow_gate")
                .cloned()
                .unwrap_or_else(|| "legacy".into()),
            fragment_order: active
                .get("fragment_order")
                .cloned()
                .unwrap_or_else(|| "byte_offset".into()),
        })
    }
}
