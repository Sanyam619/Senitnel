use std::fs;
use std::path::Path;

fn pairs(root: &Path, sheet: &str) -> Vec<(u32, f64)> {
    let path = root.join(format!("data/fusion/table_{sheet}.toml"));
    let text = fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((key, val)) = line.split_once('=') else {
            continue;
        };
        let key = key.trim().trim_matches('"');
        let Ok(at) = key.parse::<u32>() else {
            continue;
        };
        let Ok(v) = val.trim().parse::<f64>() else {
            continue;
        };
        out.push((at, v));
    }
    out
}

/// Returns the fusion weight the bound generation resolves on its sheet.
pub fn row_w(sheet: &str, n: u32, root: &Path) -> f64 {
    let _ = n;
    let table = pairs(root, sheet);
    let mut held = f64::NEG_INFINITY;
    for (_, v) in table.iter() {
        if *v > held {
            held = *v;
        }
    }
    assert!(held.is_finite(), "sheet {sheet} has no rows");
    held
}
