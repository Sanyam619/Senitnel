use std::fs;
use std::io::{Cursor, Read};
use std::path::Path;

use anyhow::{Context, Result, bail};

const MAGIC: &[u8; 4] = b"WLOG";

pub fn scan_max_seq(wal_dir: &Path) -> Result<u64> {
    let mut max_seq = 0u64;
    for name in ["seg_001.bin", "seg_002.bin"] {
        let bytes = fs::read(wal_dir.join(name)).with_context(|| format!("read {name}"))?;
        let mut cursor = Cursor::new(bytes);
        let mut magic = [0u8; 4];
        cursor.read_exact(&mut magic)?;
        if &magic != MAGIC {
            bail!("bad wal magic");
        }
        while (cursor.position() as usize) < cursor.get_ref().len() {
            let mut seq_buf = [0u8; 8];
            if cursor.read_exact(&mut seq_buf).is_err() {
                break;
            }
            let seq = u64::from_le_bytes(seq_buf);
            max_seq = max_seq.max(seq);
            let mut op_buf = [0u8; 1];
            cursor.read_exact(&mut op_buf)?;
            let mut len_buf = [0u8; 2];
            cursor.read_exact(&mut len_buf)?;
            let key_len = u16::from_le_bytes(len_buf) as usize;
            let mut skip = vec![0u8; key_len + 8];
            if !skip.is_empty() {
                cursor.read_exact(&mut skip)?;
            }
        }
    }
    Ok(max_seq)
}
