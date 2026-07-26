mod dispatch;

use std::env;
use std::path::PathBuf;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: rx-run all-layouts --out-dir <dir>");
        std::process::exit(2);
    }
    if args[1] == "all-layouts" {
        let mut out = PathBuf::from("/output");
        let mut i = 2;
        while i < args.len() {
            if args[i] == "--out-dir" && i + 1 < args.len() {
                out = PathBuf::from(&args[i + 1]);
                i += 2;
            } else {
                i += 1;
            }
        }
        let data_root = dispatch::default_data_root();
        if let Err(e) = dispatch::all_layouts(&data_root, &out) {
            eprintln!("run failed: {e}");
            std::process::exit(1);
        }
        return;
    }
    eprintln!("unknown subcommand");
    std::process::exit(2);
}
