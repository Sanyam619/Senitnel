use std::collections::HashSet;
use std::fs;
use std::io::{Cursor, Read};
use std::path::Path;

use anyhow::{Context, Result, bail};
use serde::Deserialize;

const MAGIC: &[u8; 4] = b"WLOG";

pub const SEQ_CUTOFF: &str = "seq_cutoff";

#[derive(Debug, Deserialize)]
struct SeqConfig {
    seq_cutoff: u64,
}

pub fn read_seq_cutoff(config_dir: &Path) -> Result<u64> {
    let raw = fs::read_to_string(config_dir.join("m2.toml")).context("read m2 table")?;
    let cfg: SeqConfig = toml::from_str(&raw)?;
    Ok(cfg.seq_cutoff)
}

pub struct BarrierState {
    pub cutoff: u64,
    pub applied_seq: u64,
    pub tombstones: HashSet<String>,
}

pub fn apply_k2(wal_dir: &Path, cutoff: u64) -> Result<BarrierState> {
    let mut tombstones = HashSet::new();
    let mut max_applied = 0u64;

    for name in ["seg_001.bin", "seg_002.bin"] {
        let path = wal_dir.join(name);
        let bytes = fs::read(&path).with_context(|| format!("read {name}"))?;
        let mut cursor = Cursor::new(bytes);
        let mut magic = [0u8; 4];
        cursor.read_exact(&mut magic)?;
        if &magic != MAGIC {
            bail!("bad wal magic in {name}");
        }
        while (cursor.position() as usize) < cursor.get_ref().len() {
            let pos = cursor.position();
            let mut seq_buf = [0u8; 8];
            if cursor.read_exact(&mut seq_buf).is_err() {
                break;
            }
            let seq = u64::from_le_bytes(seq_buf);
            if seq > cutoff {
                cursor.set_position(pos);
                break;
            }
            let mut op_buf = [0u8; 1];
            cursor.read_exact(&mut op_buf)?;
            let op = op_buf[0];
            let mut len_buf = [0u8; 2];
            cursor.read_exact(&mut len_buf)?;
            let key_len = u16::from_le_bytes(len_buf) as usize;
            let mut key = vec![0u8; key_len];
            if key_len > 0 {
                cursor.read_exact(&mut key)?;
            }
            let mut ts_buf = [0u8; 8];
            cursor.read_exact(&mut ts_buf)?;
            max_applied = seq;
            if op == 1 {
                tombstones.insert(String::from_utf8(key)?);
            }
        }
    }

    Ok(BarrierState {
        cutoff,
        applied_seq: max_applied,
        tombstones,
    })
}
