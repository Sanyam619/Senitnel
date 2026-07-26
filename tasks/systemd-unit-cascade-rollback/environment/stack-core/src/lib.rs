pub mod graph;
pub mod merge;
pub mod state;
pub mod unitio;
pub mod decoy;

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub struct UnitView {
    pub name: String,
    pub after: Vec<String>,
    pub requires: Vec<String>,
    pub wants: Vec<String>,
    pub binds_to: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub struct RuntimeRow {
    pub name: String,
    pub state: String,
    pub start_order: u32,
    pub hard_deps: Vec<String>,
    pub soft_deps: Vec<String>,
}

pub fn read_merged(path: &Path) -> Result<UnitView, String> {
    unitio::parse_unit(path)
}

pub fn load_runtime(runtime_root: &Path, name: &str) -> Result<RuntimeRow, String> {
    let dir = runtime_root.join(name);
    let state = fs::read_to_string(dir.join("state"))
        .map_err(|e| e.to_string())?
        .trim()
        .to_string();
    let start_order = fs::read_to_string(dir.join("order"))
        .map_err(|e| e.to_string())?
        .trim()
        .parse::<u32>()
        .map_err(|e| e.to_string())?;
    let hard = fs::read_to_string(dir.join("hard_deps"))
        .map_err(|e| e.to_string())?
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| l.trim().to_string())
        .collect();
    let soft = fs::read_to_string(dir.join("soft_deps"))
        .map_err(|e| e.to_string())?
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| l.trim().to_string())
        .collect();
    Ok(RuntimeRow {
        name: name.to_string(),
        state,
        start_order,
        hard_deps: hard,
        soft_deps: soft,
    })
}

pub fn unresolved_after_pairs(views: &HashMap<String, UnitView>, order: &[String]) -> Vec<(String, String)> {
    let pos: BTreeMap<_, _> = order.iter().enumerate().map(|(i, n)| (n.as_str(), i)).collect();
    let mut bad = Vec::new();
    for name in order {
        let view = &views[name];
        for dep in graph::op_fold::direct_after(view) {
            if !views.contains_key(&dep) {
                bad.push((name.clone(), dep));
                continue;
            }
            let Some(&dep_pos) = pos.get(dep.as_str()) else {
                bad.push((name.clone(), dep));
                continue;
            };
            let Some(&here) = pos.get(name.as_str()) else {
                continue;
            };
            if dep_pos >= here {
                bad.push((name.clone(), dep));
            }
        }
    }
    bad
}
