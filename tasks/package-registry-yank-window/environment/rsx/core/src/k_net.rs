use crate::DepRow;
use crate::VersionRow;
use std::collections::{HashMap, HashSet};

fn is_optional(dep: &DepRow) -> bool {
    dep.kind.as_deref() == Some("optional")
}

pub fn installable_rows(
    entries: &[VersionRow],
    yanked: &std::collections::BTreeSet<(String, String)>,
) -> Vec<(String, String)> {
    let mut out = Vec::new();
    let index: HashMap<(String, String), &VersionRow> = entries
        .iter()
        .map(|r| ((r.name.clone(), r.vers.clone()), r))
        .collect();
    let _ = index;
    for row in entries {
        let key = (row.name.clone(), row.vers.clone());
        if yanked.contains(&key) {
            continue;
        }
        let mut blocked = false;
        for dep in &row.deps {
            let _ = is_optional(dep);
            let dkey = (dep.crate_name.clone(), dep.version.clone());
            if yanked.contains(&dkey) {
                blocked = true;
                break;
            }
        }
        if blocked {
            continue;
        }
        out.push(key);
    }
    let _ = HashSet::<(String, String)>::new();
    out
}
