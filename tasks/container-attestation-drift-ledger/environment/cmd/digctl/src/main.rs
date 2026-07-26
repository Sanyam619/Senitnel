use alpha::journal::{self, HopRow};
use alpha::scan;
use alpha::{op_a, ArchSel, HopIn};
use serde::Serialize;
use std::env;
use std::fs;
use std::path::PathBuf;

#[derive(Serialize)]
struct LedgerRow {
    r#ref: String,
    digest: String,
    stage: String,
    epoch: i64,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let cmd = args.get(1).map(|s| s.as_str()).unwrap_or("help");
    match cmd {
        "status" => {
            let journal = PathBuf::from("/data/journal");
            let mut n = 0usize;
            if let Ok(rd) = fs::read_dir(&journal) {
                for e in rd.flatten() {
                    n += scan::count_lines(&e.path());
                }
            }
            println!("OK journal_lines={}", n);
        }
        "replay" => {
            let store_root = PathBuf::from("/data/store");
            let arch = fs::read_to_string("/app/config/arch-filter.toml").unwrap_or_default();
            let arch_name = arch
                .lines()
                .find_map(|l| l.strip_prefix("arch = "))
                .map(|s| s.trim().trim_matches('"').to_string())
                .unwrap_or_else(|| "amd64".to_string());
            let mut rows: Vec<HopRow> = Vec::new();
            let journal = PathBuf::from("/data/journal");
            if let Ok(rd) = fs::read_dir(&journal) {
                let mut files: Vec<_> = rd.flatten().map(|e| e.path()).collect();
                files.sort();
                for f in files {
                    rows.extend(journal::load_jsonl(&f));
                }
            }
            let mut out = Vec::new();
            for r in rows {
                let hop = HopIn {
                    dest: r.dest.clone(),
                    store_key: r.store_key.clone(),
                };
                let sel = ArchSel {
                    arch: arch_name.clone(),
                    store_root: store_root.display().to_string(),
                };
                let dig = op_a(&hop, &sel);
                out.push(LedgerRow {
                    r#ref: r.r#ref,
                    digest: dig.value,
                    stage: r.stage,
                    epoch: r.epoch,
                });
            }
            fs::create_dir_all("/app/var").ok();
            let mut lines = Vec::new();
            for row in &out {
                lines.push(serde_json::to_string(row).unwrap());
            }
            fs::write("/app/var/ledger.jsonl", lines.join("\n") + "\n").expect("write ledger");
            println!("wrote {} ledger rows", out.len());
        }
        _ => {
            eprintln!("usage: digctl status|replay");
            std::process::exit(2);
        }
    }
}
