use std::path::Path;

use anyhow::Result;
use serde::Serialize;
use store::{RuntimeState, column_reader, rollup};

#[derive(Serialize)]
struct PointOut {
    found: bool,
    key: Option<String>,
    value: Option<String>,
    ts: Option<u64>,
}

#[derive(Serialize)]
struct RangeOut {
    hits: Vec<HitOut>,
}

#[derive(Serialize)]
struct HitOut {
    key: String,
    value: String,
    ts: u64,
}

#[derive(Serialize)]
struct AggOut {
    count: usize,
    sum_ts: u64,
}

pub fn run_query_point(root: &Path, ks: &str, key: &str, ts: u64) -> Result<String> {
    let state = RuntimeState::load(root)?;
    let hit = column_reader::resolve_point(root, &state, ks, key, ts)?;
    let out = match hit {
        Some(h) => PointOut {
            found: true,
            key: Some(h.key),
            value: Some(h.value),
            ts: Some(h.ts),
        },
        None => PointOut {
            found: false,
            key: None,
            value: None,
            ts: None,
        },
    };
    Ok(serde_json::to_string(&out)?)
}

pub fn run_query_range(root: &Path, ks: &str, lo: &str, hi: &str, ts: u64) -> Result<String> {
    let state = RuntimeState::load(root)?;
    let hits = column_reader::resolve_range(root, &state, ks, lo, hi, ts)?;
    let out = RangeOut {
        hits: hits
            .into_iter()
            .map(|h| HitOut {
                key: h.key,
                value: h.value,
                ts: h.ts,
            })
            .collect(),
    };
    Ok(serde_json::to_string(&out)?)
}

pub fn run_query_aggregate(root: &Path, ks: &str, ts: u64) -> Result<String> {
    let state = RuntimeState::load(root)?;
    let totals = rollup::compute_totals(root, &state, ks, ts)?;
    let out = AggOut {
        count: totals.count,
        sum_ts: totals.sum_ts,
    };
    Ok(serde_json::to_string(&out)?)
}
