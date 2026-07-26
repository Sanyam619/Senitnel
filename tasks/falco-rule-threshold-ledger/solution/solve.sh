#!/bin/bash
set -euo pipefail
log_line() { printf '[oracle] %s\n' "$1"; }

patch_r3() {
  log_line "repair priority pick"
  cat > /app/mk3/body.rs <<'EOF'
pub fn W3_pick(a: i32, b: i32) -> i32 {
    if a >= b { a } else { b }
}
EOF
}

patch_k5() {
  log_line "repair cap gate"
  cat > /app/mk5/body.rs <<'EOF'
pub fn Q5_gate(emitted: i32, limit: i32, in_window: bool) -> bool {
    if !in_window {
        return true;
    }
    emitted < limit
}
EOF
}

patch_v8() {
  log_line "repair scope membership"
  cat > /app/mk8/body.rs <<'EOF'
pub fn N8_mask(cid: &str, prefix: &str, labels: &[(&str, &str)]) -> bool {
    if !cid.starts_with(prefix) {
        return false;
    }
    if labels.is_empty() {
        return true;
    }
    labels.iter().any(|(k, v)| *k == "env" && *v == "prod")
}
EOF
}

patch_h2() {
  log_line "repair mute interval"
  cat > /app/mk2/body.rs <<'EOF'
pub fn Z2_gap(probe: i64, last: i64, gap: i64) -> bool {
    if last <= 0 {
        return false;
    }
    (probe - last) < gap
}
EOF
}

patch_b1() {
  log_line "repair batch ordering"
  cat > /app/mk1/body.rs <<'EOF'
pub fn J1_seq(seqs: &[i32]) -> bool {
    if seqs.len() < 2 {
        return true;
    }
    for i in 1..seqs.len() {
        if seqs[i] <= seqs[i - 1] {
            return false;
        }
    }
    true
}
EOF
}

patch_tie() {
  log_line "repair lex tie-break"
  cat > /app/src/internal/p1.rs <<'EOF'
use crate::internal::tape::RuleDoc;
use crate::mk3;

pub fn pick_priority(a: i32, b: i32) -> i32 {
    mk3::W3_pick(a, b)
}

pub fn pick_rule<'a>(candidates: &[&'a RuleDoc]) -> Option<&'a RuleDoc> {
    if candidates.is_empty() {
        return None;
    }
    let mut best = candidates[0];
    for cand in &candidates[1..] {
        let pri = pick_priority(cand.priority, best.priority);
        if pri > best.priority || (pri == cand.priority && cand.priority > best.priority) {
            best = cand;
        } else if cand.priority == best.priority && cand.name < best.name {
            best = cand;
        }
    }
    Some(best)
}
EOF
}

patch_floor() {
  log_line "repair inclusive floor"
  cat > /app/src/internal/p3.rs <<'EOF'
use crate::internal::tape::{BatchEvent, RuleDoc};
use crate::mk8;

pub fn label_pairs(ev: &BatchEvent) -> Vec<(String, String)> {
    ev.labels.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
}

pub fn label_refs<'a>(pairs: &'a [(String, String)]) -> Vec<(&'a str, &'a str)> {
    pairs.iter().map(|(k, v)| (k.as_str(), v.as_str())).collect()
}

pub fn scope_ok(cid: &str, prefix: &str, labels: &[(&str, &str)]) -> bool {
    mk8::N8_mask(cid, prefix, labels)
}

pub fn matching_rules<'a>(
    syscall: &str,
    cid: &str,
    labels: &[(String, String)],
    rules: &'a [RuleDoc],
    floor: i32,
) -> Vec<&'a RuleDoc> {
    let refs = label_refs(labels);
    rules
        .iter()
        .filter(|r| r.syscall == syscall && r.priority >= floor)
        .filter(|r| scope_ok(cid, &r.scope_prefix, &refs))
        .collect()
}
EOF
}

patch_replay() {
  log_line "repair replay orchestration"
  cat > /app/src/internal/replay.rs <<'EOF'
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
    let mut last_alert: HashMap<(String, String, i32), i64> = HashMap::new();
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
        let key = (rule.name.clone(), ev.container_id.clone(), ev.pid);
        if p4::muted(ev.ts, *last_alert.get(&(key.0.clone(), key.1.clone(), key.2)).unwrap_or(&0), rule.suppression_sec) {
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
        times.retain(|t| ev.ts - *t <= window_sec as i64);
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

    if let Some(first) = events.first() {
        let pairs = p3::label_pairs(first);
        scope_match = p3::scope_ok(&first.container_id, SCOPE_PREFIX, &p3::label_refs(&pairs));
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
        "container_id": events.first().map(|e| e.container_id.clone()).unwrap_or_default(),
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
EOF
}

patch_seal() {
  log_line "repair seal binder"
  cat > /app/src/internal/sealpack/body.rs <<'EOF'
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
        rate_ok,
        scope_container: scope_container.to_string(),
        scope_labels: scope_labels.to_vec(),
        scope_match,
        suppression_rows: mapped,
        winning_priority: win_pri,
    };
    let pre = serde_json::to_string(&shape).unwrap_or_default();
    format!("{:x}", Sha256::digest(pre.as_bytes()))
}
EOF
}

patch_r3
patch_k5
patch_v8
patch_h2
patch_b1
patch_tie
patch_floor
patch_replay
patch_seal
bash /app/scripts/build.sh
/app/bin/frtl_audit audit --pack /app/config/default_pack.json --out /app/output/falco_threshold_report.json
test -s /app/output/falco_threshold_report.json
