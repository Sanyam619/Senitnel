use crate::internal::p1;
use crate::internal::p2;
use crate::internal::p3;
use crate::internal::p4;
use crate::internal::p5;
use crate::internal::sealpack;
use crate::internal::tape::{BatchEvent, RuleDoc};
use std::collections::HashMap;

const SCOPE_PREFIX: &str = "prod-";

pub fn replay_batch(batch_id: &str, events: &[BatchEvent], rules: &[RuleDoc], floor: i32, window_sec: i32) -> serde_json::Value {
    let seqs: Vec<i32> = events.iter().map(|e| e.seq).collect();
    let batch_order_ok = p5::ordered(&seqs);
    if !batch_order_ok {
        let scope_row = serde_json::json!({
            "container_id": events.first().map(|e| e.container_id.clone()).unwrap_or_default(),
            "scope_match": false,
            "labels_matched": [],
        });
        let body = serde_json::json!({
            "batch_id": batch_id,
            "alert_count": 0,
            "suppression_rows": [],
            "scope_row": scope_row,
            "rate_ok": false,
            "batch_order_ok": false,
            "winning_priority": 0,
            "effective_rate_window_sec": window_sec,
            "priority_floor": floor,
        });
        let digest = sealpack::bind_row(&body);
        let mut out = body.as_object().unwrap().clone();
        out.insert("digest_hex".to_string(), serde_json::Value::String(digest));
        return serde_json::Value::Object(out);
    }

    let mut sorted: Vec<&BatchEvent> = events.iter().collect();
    sorted.sort_by_key(|e| e.seq);

    let mut alert_count = 0i32;
    let mut suppression_rows: Vec<serde_json::Value> = Vec::new();
    let mut last_alert: HashMap<(String, String), i64> = HashMap::new();
    let mut rate_counts: HashMap<String, Vec<i64>> = HashMap::new();
    let mut winning_priority = 0i32;
    let mut rate_ok = true;
    let mut scope_match = false;
    let mut labels_matched: Vec<String> = Vec::new();

    for ev in sorted {
        let pairs = p3::label_pairs(ev);
        let candidates = p3::matching_rules(&ev.syscall, &ev.container_id, &pairs, rules, floor);
        if !candidates.is_empty() {
            scope_match = p3::scope_ok(&ev.container_id, SCOPE_PREFIX, &p3::label_refs(&pairs));
            for (k, v) in &pairs {
                if k == "env" && v == "prod" {
                    labels_matched.push(format!("{k}={v}"));
                }
            }
        }
        let Some(rule) = p1::pick_rule(&candidates) else { continue; };
        let key = (rule.name.clone(), ev.container_id.clone());
        if p4::muted(ev.ts, *last_alert.get(&(key.0.clone(), key.1.clone())).unwrap_or(&0), rule.suppression_sec) {
            suppression_rows.push(serde_json::json!({
                "rule": rule.name,
                "container_id": ev.container_id,
                "pid": ev.pid,
                "bound": true,
                "reason": "inside-mute",
            }));
            continue;
        }
        let times = rate_counts.entry(rule.name.clone()).or_default();
        times.retain(|t| ev.ts - *t < window_sec as i64);
        let in_window = !times.is_empty();
        if !p2::rate_gate(times.len() as i32, rule.rate_limit, in_window || times.is_empty()) {
            rate_ok = false;
            continue;
        }
        alert_count += 1;
        last_alert.insert(key, ev.ts);
        times.push(ev.ts);
        winning_priority = p1::pick_priority(rule.priority, winning_priority);
    }

    if let Some(last) = events.last() {
        let pairs = p3::label_pairs(last);
        scope_match = p3::scope_ok(&last.container_id, SCOPE_PREFIX, &p3::label_refs(&pairs));
        labels_matched = pairs
            .iter()
            .filter(|(k, v)| k == "env" && v == "prod")
            .map(|(k, v)| format!("{k}={v}"))
            .collect();
    }
    labels_matched.sort();
    labels_matched.dedup();

    suppression_rows.sort_by(|a, b| {
        let ar = a["rule"].as_str().unwrap_or("");
        let br = b["rule"].as_str().unwrap_or("");
        ar.cmp(br)
            .then_with(|| {
                a["container_id"]
                    .as_str()
                    .unwrap_or("")
                    .cmp(b["container_id"].as_str().unwrap_or(""))
            })
            .then_with(|| {
                a["pid"]
                    .as_i64()
                    .unwrap_or(0)
                    .cmp(&b["pid"].as_i64().unwrap_or(0))
            })
    });

    let scope_row = serde_json::json!({
        "container_id": events.last().map(|e| e.container_id.clone()).unwrap_or_default(),
        "scope_match": scope_match,
        "labels_matched": labels_matched,
    });
    let body = serde_json::json!({
        "batch_id": batch_id,
        "alert_count": alert_count,
        "suppression_rows": suppression_rows,
        "scope_row": scope_row,
        "rate_ok": rate_ok,
        "batch_order_ok": batch_order_ok,
        "winning_priority": winning_priority,
        "effective_rate_window_sec": window_sec,
        "priority_floor": floor,
    });
    let digest = sealpack::bind_row(&body);
    let mut out = body.as_object().unwrap().clone();
    out.insert("digest_hex".to_string(), serde_json::Value::String(digest));
    serde_json::Value::Object(out)
}

pub fn guard_ok(audits: &[serde_json::Value]) -> bool {
    let mut by_id: HashMap<String, &serde_json::Value> = HashMap::new();
    for a in audits {
        if let Some(id) = a.get("batch_id").and_then(|v| v.as_str()) {
            by_id.insert(id.to_string(), a);
        }
    }
    let mut fails = 0;
    if by_id.get("scope_miss").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()) != Some(0) {
        fails += 1;
    }
    if by_id.get("batch_skew").and_then(|a| a.get("batch_order_ok")).and_then(|v| v.as_bool()) != Some(false) {
        fails += 1;
    }
    if by_id.get("seq_plateau").and_then(|a| a.get("batch_order_ok")).and_then(|v| v.as_bool()) != Some(false) {
        fails += 1;
    }
    if by_id.get("rate_burst").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()).unwrap_or(0) > 2 {
        fails += 1;
    }
    if by_id.get("rate_edge").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()).unwrap_or(0) > 2 {
        fails += 1;
    }
    if by_id.get("suppression_hot").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()) != Some(1) {
        fails += 1;
    }
    if by_id.get("twin_pid").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()) != Some(2) {
        fails += 1;
    }
    if by_id.get("mute_edge").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()) != Some(2) {
        fails += 1;
    }
    if by_id.get("priority_pick").and_then(|a| a.get("winning_priority")).and_then(|v| v.as_i64()).unwrap_or(0) < 80 {
        fails += 1;
    }
    if by_id.get("tie_lex").and_then(|a| a.get("alert_count")).and_then(|v| v.as_i64()) != Some(1) {
        fails += 1;
    }
    fails == 0 && audits.len() >= 13
}
