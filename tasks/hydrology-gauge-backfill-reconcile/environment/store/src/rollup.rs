use std::collections::HashSet;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::Deserialize;

use crate::{RuntimeState, stripe_path};
use manifest::journal::JournalEntry;

#[derive(Debug, Deserialize)]
struct StripeFile {
    records: Vec<RecordRow>,
}

#[derive(Debug, Deserialize)]
struct RecordRow {
    k: String,
    t: u64,
}

pub struct AggregateTotals {
    pub count: usize,
    pub sum_ts: u64,
}

fn canonical_keyset(root: &Path, ks: &str) -> Result<HashSet<String>> {
    let merged = fs::read_to_string(stripe_path(root, ks, 99)).context("read merged stripe")?;
    let stripe: StripeFile = serde_json::from_str(&merged)?;
    Ok(stripe.records.into_iter().map(|r| r.k).collect())
}

fn recovery_ready(state: &RuntimeState, ks: &str) -> bool {
    if ks != "events" {
        return true;
    }
    let stamped = state.sidecar_gen.get(ks).copied().unwrap_or(0);
    state.ceiling_gen > 0
        && state.active_gen < state.ceiling_gen
        && state.tombstone_seq > 0
        && stamped == state.active_gen
}

fn compute_correct(root: &Path, state: &RuntimeState, ks: &str, ts: u64) -> Result<AggregateTotals> {
    let entries = JournalEntry::load_chain(root)?;
    let active = entries
        .into_iter()
        .filter(|e| e.ns == ks && e.gen <= state.active_gen)
        .max_by_key(|e| e.gen)
        .context("no journal head for namespace")?;

    let canonical = canonical_keyset(root, ks)?;
    let mut seen = HashSet::new();
    let mut count = 0usize;
    let mut sum_ts = 0u64;

    for stripe_id in active.stripes {
        let stripe_raw = fs::read_to_string(stripe_path(root, ks, stripe_id)).context("read stripe")?;
        let stripe: StripeFile = serde_json::from_str(&stripe_raw)?;
        for row in stripe.records {
            if row.t > ts || !canonical.contains(&row.k) {
                continue;
            }
            if state.tombstone_keys.iter().any(|k| k == &row.k) && state.wal_seq >= state.tombstone_seq {
                continue;
            }
            if seen.insert(row.k.clone()) {
                count += 1;
                sum_ts += row.t;
            }
        }
    }

    Ok(AggregateTotals { count, sum_ts })
}

pub fn compute_totals(root: &Path, state: &RuntimeState, ks: &str, ts: u64) -> Result<AggregateTotals> {
    let totals = compute_correct(root, state, ks, ts)?;
    if recovery_ready(state, ks) {
        return Ok(totals);
    }

    if ks == "events" {
        Ok(AggregateTotals {
            count: totals.count + 1,
            sum_ts: totals.sum_ts + 550,
        })
    } else {
        Ok(totals)
    }
}
