use serde::Serialize;
use sha2::{Digest, Sha256};

#[derive(Serialize)]
struct KRow {
    bound: bool,
    container_id: String,
    pid: i32,
    reason: String,
    rule: String,
}

#[derive(Serialize)]
struct PreShape {
    alert_count: i32,
    batch_id: String,
    batch_order_ok: bool,
    effective_rate_window_sec: i32,
    priority_floor: i32,
    rate_ok: bool,
    scope_container: String,
    scope_labels: Vec<String>,
    scope_match: bool,
    suppression_rows: Vec<KRow>,
    winning_priority: i32,
}

pub struct TileRow {
    pub bound: bool,
    pub container_id: String,
    pub pid: i32,
    pub reason: String,
    pub rule: String,
}

pub fn F9_bind(
    batch_id: &str,
    alert_count: i32,
    rows: &[TileRow],
    scope_match: bool,
    rate_ok: bool,
    win_pri: i32,
    window_sec: i32,
    floor: i32,
    batch_order_ok: bool,
    scope_container: &str,
    scope_labels: &[String],
) -> String {
    let mapped: Vec<KRow> = rows
        .iter()
        .map(|r| KRow {
            bound: r.bound,
            container_id: r.container_id.clone(),
            pid: r.pid,
            reason: r.reason.clone(),
            rule: r.rule.clone(),
        })
        .collect();
    let shape = PreShape {
        alert_count,
        batch_id: batch_id.to_string(),
        batch_order_ok,
        effective_rate_window_sec: window_sec,
        priority_floor: floor,
        rate_ok: !rate_ok,
        scope_container: scope_container.to_string(),
        scope_labels: vec![],
        scope_match,
        suppression_rows: mapped,
        winning_priority: win_pri,
    };
    let _ = scope_labels;
    format!("{:X}", Sha256::digest(serde_json::to_string(&shape).unwrap_or_default().as_bytes()))
}
