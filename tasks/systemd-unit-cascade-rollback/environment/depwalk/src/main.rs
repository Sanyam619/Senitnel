use stack_core::graph::op_fold;
use stack_core::merge::op_alias;
use stack_core::unitio;
use std::collections::HashMap;
use std::env;
use std::path::PathBuf;

fn main() {
    let mut units_root = PathBuf::from("/data/stack/units");
    let mut runtime_root = PathBuf::from("/data/stack/runtime");
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--units-root" => {
                i += 1;
                units_root = PathBuf::from(&args[i]);
            }
            "--runtime-root" => {
                i += 1;
                runtime_root = PathBuf::from(&args[i]);
            }
            _ => {}
        }
        i += 1;
    }
    let names = [
        "journal.service",
        "store.service",
        "cache.service",
        "ingress.service",
        "relay.service",
        "stack.target",
    ];
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let path = if merged.exists() {
            merged
        } else {
            units_root.join(name)
        };
        let mut view = unitio::parse_unit(&path).expect("parse unit");
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.to_string(), view);
    }
    let name_list: Vec<String> = names.iter().map(|s| s.to_string()).collect();
    let order = op_fold::topo(&name_list, &views)
        .unwrap_or_else(|e| {
            eprintln!("depwalk: {e}");
            std::process::exit(1);
        });
    let bad = stack_core::unresolved_after_pairs(&views, &order);
    if !bad.is_empty() {
        for (a, b) in bad {
            eprintln!("unresolved After edge: {a} -> {b}");
        }
        std::process::exit(1);
    }
    println!("depwalk ok");
}
