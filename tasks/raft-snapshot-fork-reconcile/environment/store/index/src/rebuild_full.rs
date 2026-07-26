use std::collections::HashMap;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use manifest::journal::JournalEntry;
use serde::Deserialize;
use sha2::{Digest as Sha2Digest, Sha256};

use crate::sidecar::{SidecarFile, save};

#[derive(Debug, Deserialize)]
struct StripeFile {
    id: u64,
    records: Vec<RecordRow>,
}

#[derive(Debug, Deserialize)]
struct RecordRow {
    k: String,
}

pub struct DigestReport {
    pub hex: String,
    pub segment_count: usize,
}

pub fn run_p4(
    data_root: &Path,
    ks: &str,
    after_barrier: u64,
    tombstones: &[String],
    wal_seq: u64,
    tombstone_seq: u64,
) -> Result<DigestReport> {
    let stripes = JournalEntry::stripes_at(data_root, ks, after_barrier)?;
    let mut map = HashMap::new();
    let mut hasher = Sha256::new();

    for stripe_id in &stripes {
        let path = if *stripe_id == 99 {
            data_root.join("columns").join(format!("{ks}_merged.col"))
        } else {
            data_root.join("columns").join(format!("{ks}_{stripe_id:03}.col"))
        };
        let raw = fs::read(&path).with_context(|| format!("read stripe {stripe_id}"))?;
        hasher.update(&raw);
        let stripe: StripeFile = serde_json::from_slice(&raw)?;
        for row in stripe.records {
            if tombstones.iter().any(|k| k == &row.k) && wal_seq >= tombstone_seq && tombstone_seq > 0 {
                continue;
            }
            map.insert(row.k, stripe.id);
        }
    }

    let digest_hex = hex::encode(hasher.finalize());
    let sidecar = SidecarFile {
        bound_gen: after_barrier,
        map,
        digest: digest_hex.clone(),
    };
    save(data_root, ks, &sidecar)?;

    Ok(DigestReport {
        hex: digest_hex,
        segment_count: stripes.len(),
    })
}
