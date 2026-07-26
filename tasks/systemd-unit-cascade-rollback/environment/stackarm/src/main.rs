use stack_core::state::op_activate;
use std::env;
use std::path::PathBuf;

fn main() {
    let mut runtime_root = PathBuf::from("/data/stack/runtime");
    let mut target = "stack.target".to_string();
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--runtime-root" => {
                i += 1;
                runtime_root = PathBuf::from(&args[i]);
            }
            "--target" => {
                i += 1;
                target = args[i].clone();
            }
            "--units-root" => {
                i += 1;
            }
            _ => {}
        }
        i += 1;
    }
    let names = vec![
        "journal.service".to_string(),
        "store.service".to_string(),
        "cache.service".to_string(),
        "ingress.service".to_string(),
        "relay.service".to_string(),
        target,
    ];
    let order = op_activate::arm(&runtime_root, &names).map_err(|e| {
        eprintln!("stackarm: {e}");
        std::process::exit(1);
    }).unwrap();
    op_activate::activate_all(&runtime_root, &names, &order).map_err(|e| {
        eprintln!("stackarm: {e}");
        std::process::exit(1);
    }).unwrap();
    println!("stackarm ok");
}
