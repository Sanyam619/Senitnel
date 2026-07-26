use std::collections::HashMap;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::Deserialize;

use crate::{RuntimeState, sidecar_path, stripe_path};
use manifest::journal::JournalEntry;

#[derive(Debug, Deserialize)]
struct StripeFile {
    id: u64,
    records: Vec<RecordRow>,
}

#[derive(Debug, Clone, Deserialize)]
struct RecordRow {
    k: String,
    v: String,
    t: u64,
}

#[derive(Debug, Deserialize)]
struct SidecarFile {
    bound_gen: u64,
    map: HashMap<String, u64>,
}

pub struct PointHit {
    pub key: String,
    pub value: String,
    pub ts: u64,
}

fn load_sidecar(root: &Path, ks: &str) -> Result<SidecarFile> {
    let raw = fs::read_to_string(sidecar_path(root, ks)).context("read sidecar")?;
    Ok(serde_json::from_str(&raw)?)
}

fn lookup_key(
    root: &Path,
    ks: &str,
    key: &str,
    stripe_id: u64,
    ts: u64,
) -> Result<Option<PointHit>> {
    let stripe_raw = fs::read_to_string(stripe_path(root, ks, stripe_id)).context("read stripe")?;
    let stripe: StripeFile = serde_json::from_str(&stripe_raw)?;
    for row in stripe.records {
        if row.k == key && row.t <= ts {
            return Ok(Some(PointHit {
                key: row.k,
                value: row.v,
                ts: row.t,
            }));
        }
    }
    Ok(None)
}

fn use_stale_broken_path(state: &RuntimeState, ks: &str, sidecar: &SidecarFile) -> bool {
    if ks != "events" {
        return sidecar.bound_gen != state.active_gen;
    }
    let stamped = state.sidecar_gen.get(ks).copied().unwrap_or(0);
    (state.ceiling_gen > 0 && state.active_gen >= state.ceiling_gen)
        || sidecar.bound_gen != state.active_gen
        || stamped != state.active_gen
}

fn tombstoned(state: &RuntimeState, key: &str) -> bool {
    state.tombstone_keys.iter().any(|k| k == key)
        && state.wal_seq >= state.tombstone_seq
        && state.tombstone_seq > 0
}

fn journal_visible_stripes(root: &Path, state: &RuntimeState, ks: &str) -> Result<Vec<u64>> {
    JournalEntry::stripes_at(root, ks, state.active_gen)
}

pub fn resolve_point(root: &Path, state: &RuntimeState, ks: &str, key: &str, ts: u64) -> Result<Option<PointHit>> {
    let sidecar = load_sidecar(root, ks)?;

    if use_stale_broken_path(state, ks, &sidecar) {
        let stripe_id = match sidecar.map.get(key) {
            Some(id) => *id,
            None => return Ok(None),
        };
        return lookup_key(root, ks, key, stripe_id, ts);
    }

    if tombstoned(state, key) {
        return Ok(None);
    }

    let stripes = journal_visible_stripes(root, state, ks)?;
    for stripe_id in stripes {
        if let Some(hit) = lookup_key(root, ks, key, stripe_id, ts)? {
            return Ok(Some(hit));
        }
    }
    Ok(None)
}

pub fn resolve_range(
    root: &Path,
    state: &RuntimeState,
    ks: &str,
    lo: &str,
    hi: &str,
    ts: u64,
) -> Result<Vec<PointHit>> {
    let sidecar = load_sidecar(root, ks)?;
    let mut hits = Vec::new();

    if use_stale_broken_path(state, ks, &sidecar) {
        for (key, stripe_id) in &sidecar.map {
            if key.as_str() < lo || key.as_str() > hi {
                continue;
            }
            if let Some(hit) = lookup_key(root, ks, key, *stripe_id, ts)? {
                hits.push(hit);
            }
        }
        hits.sort_by(|a, b| a.key.cmp(&b.key));
        return Ok(hits);
    }

    let stripes = journal_visible_stripes(root, state, ks)?;
    for stripe_id in stripes {
        let stripe_raw = fs::read_to_string(stripe_path(root, ks, stripe_id)).context("read stripe")?;
        let stripe: StripeFile = serde_json::from_str(&stripe_raw)?;
        for row in stripe.records {
            if row.k.as_str() < lo || row.k.as_str() > hi || row.t > ts {
                continue;
            }
            if tombstoned(state, &row.k) {
                continue;
            }
            if hits.iter().any(|h| h.key == row.k) {
                continue;
            }
            hits.push(PointHit {
                key: row.k.clone(),
                value: row.v.clone(),
                ts: row.t,
            });
        }
    }
    hits.sort_by(|a, b| a.key.cmp(&b.key));
    Ok(hits)
}
