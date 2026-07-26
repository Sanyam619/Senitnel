use serde_json::Value;
use std::collections::BTreeSet;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

#[derive(Debug, Clone)]
pub struct Evt {
    pub tag: String,
    pub epoch: u64,
    pub lab: Option<String>,
}

pub fn take_c(path: &Path) -> Result<Vec<Evt>, String> {
    let f = File::open(path).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in BufReader::new(f).lines() {
        let line = line.map_err(|e| e.to_string())?;
        if line.trim().is_empty() {
            continue;
        }
        let v: Value = serde_json::from_str(&line).map_err(|e| e.to_string())?;
        let tag = v
            .get("tag")
            .and_then(|x| x.as_str())
            .unwrap_or("")
            .to_string();
        let epoch = v.get("epoch").and_then(|x| x.as_u64()).unwrap_or(0);
        let lab = v
            .get("lab")
            .and_then(|x| x.as_str())
            .map(|s| s.to_string());
        out.push(Evt { tag, epoch, lab });
    }
    Ok(out)
}

pub fn skim_cap(rows: &[Evt]) -> Vec<String> {
    let fence = rows
        .iter()
        .filter(|r| r.tag == "seal")
        .map(|r| r.epoch)
        .max();
    let mut set = BTreeSet::new();
    for r in rows {
        if r.tag != "admit" && r.tag != "reclaim" {
            continue;
        }
        if let Some(se) = fence {
            if r.epoch > se {
                continue;
            }
        }
        if let Some(lab) = &r.lab {
            set.insert(lab.clone());
        }
    }
    set.into_iter().collect()
}
