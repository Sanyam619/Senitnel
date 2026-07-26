use clap::{Parser, Subcommand};
use core::build_report;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Parser)]
#[command(name = "syncctl")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Status,
    Report {
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Status => {
            let report = build_report(Path::new("/app/data"), Path::new("/app/config/l7"))
                .expect("status");
            println!("{{\"branch_gen\":{}}}", report.branch_gen);
        }
        Commands::Report { out } => {
            let report = build_report(Path::new("/app/data"), Path::new("/app/config/l7"))
                .expect("report");
            let payload = serde_json::to_string_pretty(&report).expect("json");
            fs::write(&out, format!("{payload}\n")).expect("write");
        }
    }
}
