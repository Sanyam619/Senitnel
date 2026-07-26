#!/bin/bash
set -euo pipefail
cat > /app/core/atlas.rs <<'RS'
use crate::model::{span, CaseData, Node};

pub fn phase_b<'a>(data: &'a CaseData, zone: &str, id: &str, t: i64) -> Option<&'a Node> {
    let mut items: Vec<&Node> = data.nodes.iter()
        .filter(|n| n.zone == zone)
        .filter(|n| n.id == id)
        .filter(|n| span(t, n.start, n.end))
        .filter(|n| n.withdrawn_after.map(|cut| t < cut).unwrap_or(true))
        .collect();
    items.sort_by(|a, b| {
        a.start.cmp(&b.start)
            .then_with(|| a.end.cmp(&b.end))
            .then_with(|| a.id.cmp(&b.id))
    });
    items.pop()
}

pub fn phase_f<'a>(data: &'a CaseData, zone: &str, id: &str, t: i64) -> Option<&'a Node> {
    data.nodes.iter()
        .filter(|n| n.zone == zone)
        .filter(|n| n.id == id)
        .filter(|n| span(t, n.start, n.end))
        .filter(|n| n.withdrawn_after.map(|cut| t >= cut).unwrap_or(false))
        .min_by(|a, b| a.id.cmp(&b.id))
}

pub fn phase_e(data: &CaseData, zone: &str, name: &str) -> bool {
    data.records.iter()
        .any(|r| r.zone == zone && r.name == name && !r.body.is_empty())
}
RS
cat > /app/core/phase.rs <<'RS'
use crate::model::{span, CaseData, Mark, Query};

pub fn phase_a(data: &CaseData, q: &Query) -> Vec<Mark> {
    let mut out: Vec<Mark> = data.marks.iter()
        .filter(|m| m.name == q.name)
        .filter(|m| span(q.instant, m.start, m.end))
        .filter(|m| data.records.iter().any(|r| r.zone == m.zone && r.name == m.name))
        .cloned()
        .collect();
    out.sort_by(|a, b| {
        a.start.cmp(&b.start)
            .then_with(|| a.label.cmp(&b.label))
            .then_with(|| a.signer.cmp(&b.signer))
    });
    out
}
RS
cat > /app/clock/sieve.rs <<'RS'
use crate::core::atlas::{phase_b, phase_e};
use crate::model::{span, CaseData, Mark, Query};

fn root_line(data: &CaseData, zone: &str, id: &str, digest: &str, t: i64) -> Option<String> {
    let mut roots: Vec<_> = data.roots.iter()
        .filter(|r| r.zone == zone)
        .filter(|r| r.child == id)
        .filter(|r| r.digest == digest)
        .filter(|r| span(t, r.start, r.end))
        .collect();
    roots.sort_by(|a, b| a.start.cmp(&b.start).then_with(|| a.child.cmp(&b.child)));
    roots.pop().map(|r| format!("root:{}->{}", r.zone, r.child))
}

fn bridge_line(data: &CaseData, zone: &str, child: &str, issuer: &str, t: i64) -> Option<String> {
    let mut links: Vec<_> = data.bridges.iter()
        .filter(|b| b.zone == zone)
        .filter(|b| b.child == child)
        .filter(|b| b.issuer == issuer)
        .filter(|b| span(t, b.start, b.end))
        .collect();
    links.sort_by(|a, b| a.start.cmp(&b.start).then_with(|| a.child.cmp(&b.child)));
    links.pop().map(|b| format!("{}->{}", b.issuer, b.child))
}

pub fn fold_c(data: &CaseData, q: &Query, mark: &Mark) -> Option<Vec<String>> {
    if !phase_e(data, &mark.zone, &q.name) {
        return None;
    }
    let signer = phase_b(data, &mark.zone, &mark.signer, q.instant)?;
    if signer.role != "ZSK" {
        return None;
    }
    let mut issuers: Vec<_> = data.bridges.iter()
        .filter(|b| b.zone == mark.zone)
        .filter(|b| b.child == signer.id)
        .filter(|b| span(q.instant, b.start, b.end))
        .map(|b| b.issuer.clone())
        .collect();
    issuers.sort();
    issuers.dedup();
    for issuer_id in issuers {
        if let Some(issuer) = phase_b(data, &mark.zone, &issuer_id, q.instant) {
            if issuer.role != "KSK" {
                continue;
            }
            let a = root_line(data, &mark.zone, &issuer.id, &issuer.digest, q.instant);
            let b = bridge_line(data, &mark.zone, &signer.id, &issuer.id, q.instant);
            if let (Some(root), Some(link)) = (a, b) {
                return Some(vec![root, link, format!("{}->{}", signer.id, mark.name)]);
            }
        }
    }
    None
}
RS
cat > /app/report/emit.rs <<'RS'
use crate::clock::sieve::fold_c;
use crate::core::atlas::phase_f;
use crate::core::phase::phase_a;
use crate::model::{CaseData, Mark, Outcome, Query};

fn esc(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}

fn pack_a(rows: &[Outcome]) -> String {
    let mut out = String::from("[\n");
    for (i, r) in rows.iter().enumerate() {
        if i > 0 {
            out.push_str(",\n");
        }
        let chain = r.chain.iter()
            .map(|v| format!("\"{}\"", esc(v)))
            .collect::<Vec<_>>()
            .join(",");
        out.push_str(&format!(
            "  {{\"id\":\"{}\",\"name\":\"{}\",\"instant\":{},\"status\":\"{}\",\"chain\":[{}],\"reason\":\"{}\"}}",
            esc(&r.id), esc(&r.name), r.instant, esc(&r.status), chain, esc(&r.reason)
        ));
    }
    out.push_str("\n]\n");
    out
}

fn pack_b(ids: &[String]) -> String {
    let body = ids.iter()
        .map(|v| format!("\"{}\"", esc(v)))
        .collect::<Vec<_>>()
        .join(",");
    format!("{{\"queries\":[{}]}}\n", body)
}

fn stale_route(data: &CaseData, q: &Query, marks: &[Mark]) -> bool {
    marks.iter().any(|m| phase_f(data, &m.zone, &m.signer, q.instant).is_some())
}

fn row_for(data: &CaseData, q: &Query) -> (Outcome, bool) {
    let marks = phase_a(data, q);
    let mut row = Outcome {
        id: q.id.clone(),
        name: q.name.clone(),
        instant: q.instant,
        status: "invalid".to_string(),
        chain: Vec::new(),
        reason: "no_path".to_string(),
    };
    let mut choices = Vec::new();
    for mark in &marks {
        if let Some(chain) = fold_c(data, q, mark) {
            choices.push((mark.clone(), chain));
        }
    }
    choices.sort_by(|a, b| {
        a.0.start.cmp(&b.0.start)
            .then_with(|| a.0.label.cmp(&b.0.label))
            .then_with(|| a.0.signer.cmp(&b.0.signer))
    });
    if let Some((mark, chain)) = choices.pop() {
        row.status = "valid".to_string();
        row.chain = chain;
        row.reason = mark.label;
        return (row, false);
    }
    if stale_route(data, q, &marks) {
        row.reason = "replayed".to_string();
        return (row, true);
    }
    (row, false)
}

pub fn emit_d(data: &CaseData) -> (String, String) {
    let mut rows = Vec::new();
    let mut replayed = Vec::new();
    for q in &data.queries {
        let (row, replay) = row_for(data, q);
        if replay {
            replayed.push(q.id.clone());
        }
        rows.push(row);
    }
    replayed.sort();
    (pack_a(&rows), pack_b(&replayed))
}
RS
cargo run --quiet --manifest-path /app/Cargo.toml -- /app/data/queries.tsv /app/output
