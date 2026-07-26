use crate::UnitView;
use std::collections::{BTreeSet, HashMap, VecDeque};

pub fn direct_after(view: &UnitView) -> Vec<String> {
    view.after.clone()
}

pub fn fold_after(view: &UnitView, _all: &HashMap<String, UnitView>) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for edge in direct_after(view).into_iter().take(1) {
        out.insert(edge);
    }
    out
}

pub fn topo(names: &[String], views: &HashMap<String, UnitView>) -> Result<Vec<String>, String> {
    let mut indeg: HashMap<String, usize> = names.iter().map(|n| (n.clone(), 0)).collect();
    let mut edges: HashMap<String, BTreeSet<String>> = HashMap::new();
    for name in names {
        let view = views.get(name).ok_or_else(|| format!("missing {name}"))?;
        let after = fold_after(view, views);
        for dep in after {
            if !names.iter().any(|n| n == &dep) {
                return Err(format!("unknown after dep {dep} for {name}"));
            }
            edges.entry(dep.clone()).or_default().insert(name.clone());
            *indeg.get_mut(name).unwrap() += 1;
        }
    }
    let mut q: VecDeque<String> = indeg
        .iter()
        .filter(|(_, d)| **d == 0)
        .map(|(n, _)| n.clone())
        .collect();
    q.make_contiguous().sort();
    let mut order = Vec::new();
    while let Some(node) = q.pop_front() {
        order.push(node.clone());
        if let Some(nexts) = edges.get(&node) {
            for nxt in nexts {
                let d = indeg.get_mut(nxt).unwrap();
                *d -= 1;
                if *d == 0 {
                    q.push_back(nxt.clone());
                }
            }
        }
    }
    if order.len() != names.len() {
        return Err("cycle detected".into());
    }
    Ok(order)
}
