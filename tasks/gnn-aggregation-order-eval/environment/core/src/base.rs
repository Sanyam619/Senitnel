use std::fs;
use std::path::Path;

#[derive(Clone)]
pub struct Mark {
    pub idx: u32,
    pub state: String,
    pub tip: String,
    pub sheet: String,
    pub agg: String,
    pub norm: String,
    pub weft_c: Vec<String>,
    pub weft_d: Vec<String>,
}

#[derive(Clone)]
pub struct Lot {
    pub name: String,
    pub feats: Vec<Vec<f32>>,
    pub labels: Vec<u16>,
    pub edges: Vec<(u32, u32)>,
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
            agg: field_str(line, "agg").unwrap_or_default(),
            norm: field_str(line, "norm").unwrap_or_default(),
            weft_c: field_list(line, "weft_c"),
            weft_d: field_list(line, "weft_d"),
        });
    }
    out
}

pub fn rd_u32(blob: &[u8], off: &mut usize) -> u32 {
    let v = u32::from_le_bytes(blob[*off..*off + 4].try_into().unwrap_or([0; 4]));
    *off += 4;
    v
}

pub fn rd_u16(blob: &[u8], off: &mut usize) -> u16 {
    let v = u16::from_le_bytes(blob[*off..*off + 2].try_into().unwrap_or([0; 2]));
    *off += 2;
    v
}

pub fn rd_f32(blob: &[u8], off: &mut usize) -> f32 {
    let v = f32::from_le_bytes(blob[*off..*off + 4].try_into().unwrap_or([0; 4]));
    *off += 4;
    v
}

pub fn rd_rowf(blob: &[u8], off: &mut usize, dim: usize) -> Vec<f32> {
    let mut row = Vec::with_capacity(dim);
    for _ in 0..dim {
        row.push(rd_f32(blob, off));
    }
    row
}

pub fn read_blob(path: &Path) -> Vec<u8> {
    fs::read(path).unwrap_or_default()
}

pub fn read_graph(path: &Path, name: &str) -> Lot {
    let blob = read_blob(path);
    if blob.len() < 20 || &blob[0..4] != b"GPH1" {
        return Lot {
            name: name.to_string(),
            feats: Vec::new(),
            labels: Vec::new(),
            edges: Vec::new(),
        };
    }
    let mut off = 4usize;
    let n = rd_u32(&blob, &mut off) as usize;
    let e = rd_u32(&blob, &mut off) as usize;
    let d = rd_u32(&blob, &mut off) as usize;
    let _nc = rd_u32(&blob, &mut off);
    let mut feats = Vec::with_capacity(n);
    for _ in 0..n {
        feats.push(rd_rowf(&blob, &mut off, d));
    }
    let mut labels = Vec::with_capacity(n);
    for _ in 0..n {
        labels.push(rd_u16(&blob, &mut off));
    }
    let mut edges = Vec::with_capacity(e);
    for _ in 0..e {
        let u = rd_u32(&blob, &mut off);
        let v = rd_u32(&blob, &mut off);
        edges.push((u, v));
    }
    Lot {
        name: name.to_string(),
        feats,
        labels,
        edges,
    }
}

pub fn fold_graphs(lots: &[Lot], label: &str) -> Lot {
    let mut feats = Vec::new();
    let mut labels = Vec::new();
    let mut edges = Vec::new();
    let mut off = 0u32;
    for lot in lots {
        let n = lot.feats.len() as u32;
        feats.extend(lot.feats.iter().cloned());
        labels.extend(lot.labels.iter().cloned());
        for &(u, v) in &lot.edges {
            edges.push((u + off, v + off));
        }
        off += n;
    }
    Lot {
        name: label.to_string(),
        feats,
        labels,
        edges,
    }
}
