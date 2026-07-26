use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct Mark {
    pub idx: u32,
    pub state: String,
    pub tip: String,
    pub sheet: String,
    pub weft_c: Vec<String>,
    pub weft_d: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct Lot {
    pub name: String,
    pub tags: Vec<u16>,
    pub lw: Vec<f32>,
    pub rows: Vec<Vec<f32>>,
}

fn field_at<'a>(line: &'a str, key: &str) -> Option<&'a str> {
    let pat = format!("\"{key}\":");
    let start = line.find(&pat)? + pat.len();
    Some(line[start..].trim_start())
}

pub fn field_u32(line: &str, key: &str) -> Option<u32> {
    let rest = field_at(line, key)?;
    let end = rest
        .find(|c: char| !c.is_ascii_digit())
        .unwrap_or(rest.len());
    rest[..end].parse().ok()
}

pub fn field_str(line: &str, key: &str) -> Option<String> {
    let rest = field_at(line, key)?;
    let rest = rest.strip_prefix('"')?;
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

pub fn field_list(line: &str, key: &str) -> Vec<String> {
    let mut out = Vec::new();
    let Some(rest) = field_at(line, key) else {
        return out;
    };
    let Some(rest) = rest.strip_prefix('[') else {
        return out;
    };
    let Some(end) = rest.find(']') else {
        return out;
    };
    let body = &rest[..end];
    let mut cur = body;
    while let Some(q0) = cur.find('"') {
        let after = &cur[q0 + 1..];
        let Some(q1) = after.find('"') else {
            break;
        };
        out.push(after[..q1].to_string());
        cur = &after[q1 + 1..];
    }
    out
}

pub fn read_marks(path: &Path) -> Vec<Mark> {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let Some(idx) = field_u32(line, "idx") else {
            continue;
        };
        out.push(Mark {
            idx,
            state: field_str(line, "state").unwrap_or_default(),
            tip: field_str(line, "tip").unwrap_or_default(),
            sheet: field_str(line, "sheet").unwrap_or_default(),
            weft_c: field_list(line, "weft_c"),
            weft_d: field_list(line, "weft_d"),
        });
    }
    out
}

pub fn rd_u32(b: &[u8], off: &mut usize) -> u32 {
    let v = u32::from_le_bytes([b[*off], b[*off + 1], b[*off + 2], b[*off + 3]]);
    *off += 4;
    v
}

pub fn rd_u16(b: &[u8], off: &mut usize) -> u16 {
    let v = u16::from_le_bytes([b[*off], b[*off + 1]]);
    *off += 2;
    v
}

pub fn rd_f32(b: &[u8], off: &mut usize) -> f32 {
    let v = f32::from_le_bytes([b[*off], b[*off + 1], b[*off + 2], b[*off + 3]]);
    *off += 4;
    v
}

pub fn rd_rowf(b: &[u8], off: &mut usize, dim: usize) -> Vec<f32> {
    let mut row = Vec::with_capacity(dim);
    for _ in 0..dim {
        row.push(rd_f32(b, off));
    }
    row
}

pub fn read_blob(path: &Path) -> Vec<u8> {
    fs::read(path).unwrap_or_default()
}

pub fn read_lot(path: &Path, name: &str) -> Option<Lot> {
    let b = fs::read(path).ok()?;
    if b.len() < 12 || &b[0..4] != b"SGB1" {
        return None;
    }
    let mut off = 4usize;
    let n = rd_u32(&b, &mut off) as usize;
    let dim = rd_u32(&b, &mut off) as usize;
    let mut tags = Vec::with_capacity(n);
    let mut lw = Vec::with_capacity(n);
    let mut rows = Vec::with_capacity(n);
    for _ in 0..n {
        tags.push(rd_u16(&b, &mut off));
        lw.push(rd_f32(&b, &mut off));
        rows.push(rd_rowf(&b, &mut off, dim));
    }
    Some(Lot {
        name: name.to_string(),
        tags,
        lw,
        rows,
    })
}

pub fn read_dir_lots(dir: &Path, prefix: &str) -> Vec<Lot> {
    let mut names: Vec<String> = fs::read_dir(dir)
        .map(|it| {
            it.filter_map(|e| e.ok())
                .filter_map(|e| e.file_name().into_string().ok())
                .filter(|n| n.ends_with(".bin"))
                .collect()
        })
        .unwrap_or_default();
    names.sort();
    let mut out = Vec::new();
    for n in names {
        let stem = n.trim_end_matches(".bin");
        let full = format!("{prefix}/{stem}");
        if let Some(lot) = read_lot(&dir.join(&n), &full) {
            out.push(lot);
        }
    }
    out
}

pub fn fold_all(lots: &[Lot], name: &str) -> Lot {
    let mut out = Lot {
        name: name.to_string(),
        tags: Vec::new(),
        lw: Vec::new(),
        rows: Vec::new(),
    };
    for lot in lots {
        out.tags.extend_from_slice(&lot.tags);
        out.lw.extend_from_slice(&lot.lw);
        out.rows.extend_from_slice(&lot.rows);
    }
    out
}

pub fn read_tags(blob: &[u8]) -> Vec<u16> {
    if blob.len() < 12 {
        return Vec::new();
    }
    let magic = &blob[0..4];
    let mut off = 4usize;
    let n = rd_u32(blob, &mut off) as usize;
    let _dim = rd_u32(blob, &mut off) as usize;
    if magic == b"CKP2" {
        let _block = rd_u32(blob, &mut off) as usize;
    } else if magic != b"CKP1" {
        return Vec::new();
    }
    let mut tags = Vec::with_capacity(n);
    for _ in 0..n {
        tags.push(rd_u16(blob, &mut off));
    }
    tags
}
