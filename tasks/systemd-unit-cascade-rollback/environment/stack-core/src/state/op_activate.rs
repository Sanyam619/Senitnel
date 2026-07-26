use crate::graph::op_fold;
use crate::merge::op_alias;
use crate::unitio;
use crate::{RuntimeRow, UnitView};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub fn arm(runtime_root: &Path, names: &[String]) -> Result<Vec<String>, String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.clone(), view);
    }
    op_fold::topo(names, &views)
}

pub fn write_row(runtime_root: &Path, name: &str, order: u32, view: &UnitView) -> Result<(), String> {
    let dir = runtime_root.join(name);
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    fs::write(dir.join("state"), "active\n").map_err(|e| e.to_string())?;
    fs::write(dir.join("order"), format!("{order}\n")).map_err(|e| e.to_string())?;
    let hard = view
        .requires
        .iter()
        .chain(view.binds_to.iter())
        .cloned()
        .collect::<Vec<_>>();
    fs::write(dir.join("hard_deps"), format!("{}\n", hard.join("\n"))).map_err(|e| e.to_string())?;
    fs::write(dir.join("soft_deps"), format!("{}\n", view.wants.join("\n"))).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn activate_all(runtime_root: &Path, names: &[String], order: &[String]) -> Result<(), String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.clone(), view);
    }
    for (idx, name) in order.iter().enumerate() {
        let view = views.get(name).unwrap();
        write_row(runtime_root, name, (idx + 1) as u32, view)?;
    }
    Ok(())
}
