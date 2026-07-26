use crate::UnitView;
use std::fs;
use std::path::Path;

pub fn parse_unit(path: &Path) -> Result<UnitView, String> {
    let name = path
        .file_name()
        .and_then(|s| s.to_str())
        .ok_or("bad path")?
        .trim_end_matches(".ini")
        .to_string();
    if name == "merged" {
        let parent = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("unknown.service");
        return parse_body(parent, &fs::read_to_string(path).map_err(|e| e.to_string())?);
    }
    parse_body(&name, &fs::read_to_string(path).map_err(|e| e.to_string())?)
}

fn parse_body(name: &str, body: &str) -> Result<UnitView, String> {
    let mut after = Vec::new();
    let mut requires = Vec::new();
    let mut wants = Vec::new();
    let mut binds_to = Vec::new();
    for line in body.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') || line.starts_with('[') {
            continue;
        }
        let Some((k, v)) = line.split_once('=') else { continue };
        let vals: Vec<String> = v.split_whitespace().map(|s| s.to_string()).collect();
        match k.trim() {
            "After" => after.extend(vals),
            "Requires" => requires.extend(vals),
            "Wants" => wants.extend(vals),
            "BindsTo" => binds_to.extend(vals),
            _ => {}
        }
    }
    Ok(UnitView {
        name: name.to_string(),
        after,
        requires,
        wants,
        binds_to,
    })
}
