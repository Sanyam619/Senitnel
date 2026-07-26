use crate::internal::tape::RuleDoc;
use std::fs;

pub fn load_rules(path: &str) -> Result<Vec<RuleDoc>, Box<dyn std::error::Error>> {
    let raw = fs::read_to_string(path)?;
    let v: serde_json::Value = serde_json::from_str(&raw)?;
    let mut out = Vec::new();
    if let Some(arr) = v.get("rules").and_then(|r| r.as_array()) {
        for item in arr {
            out.push(RuleDoc {
                name: item.get("name").and_then(|x| x.as_str()).unwrap_or("").to_string(),
                priority: item.get("priority").and_then(|x| x.as_i64()).unwrap_or(0) as i32,
                syscall: item.get("syscall").and_then(|x| x.as_str()).unwrap_or("").to_string(),
                rate_limit: item.get("rate_limit").and_then(|x| x.as_i64()).unwrap_or(1) as i32,
                suppression_sec: item.get("suppression_sec").and_then(|x| x.as_i64()).unwrap_or(0) as i64,
                scope_prefix: item.get("scope_prefix").and_then(|x| x.as_str()).unwrap_or("").to_string(),
            });
        }
    }
    Ok(out)
}

pub fn load_floor(path: &str) -> Result<i32, Box<dyn std::error::Error>> {
    for line in fs::read_to_string(path)?.lines() {
        if line.starts_with("priority_floor") {
            return Ok(line.split('=').nth(1).unwrap_or("0").trim().parse()?);
        }
    }
    Ok(40)
}

pub fn load_window(path: &str) -> Result<i32, Box<dyn std::error::Error>> {
    for line in fs::read_to_string(path)?.lines() {
        if line.starts_with("rate_window_sec") {
            return Ok(line.split('=').nth(1).unwrap_or("0").trim().parse()?);
        }
    }
    Ok(60)
}
