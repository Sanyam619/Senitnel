use stack_core::RuntimeRow;
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    let mut runtime_root = PathBuf::from("/data/stack/runtime");
    let mut out = PathBuf::from("/output/rollback-report.json");
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--runtime-root" => {
                i += 1;
                runtime_root = PathBuf::from(&args[i]);
            }
            "--out" => {
                i += 1;
                out = PathBuf::from(&args[i]);
            }
            _ => {}
        }
        i += 1;
    }
    let names = [
        "stack.target",
        "ingress.service",
        "cache.service",
        "store.service",
        "journal.service",
        "relay.service",
    ];
    let mut units = Vec::new();
    for name in names {
        units.push(stack_core::load_runtime(&runtime_root, name).expect("runtime row"));
    }
    units.sort_by_key(|r| r.start_order);
    let doc = serde_json::json!({
        "version": 1,
        "units": units,
    });
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent).ok();
    }
    fs::write(&out, serde_json::to_string_pretty(&doc).unwrap()).unwrap();
    println!("ledger ok");
}
