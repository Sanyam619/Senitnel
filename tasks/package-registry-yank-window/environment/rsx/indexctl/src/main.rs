use clap::{Parser, Subcommand};
use core::write_report;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "indexctl")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Report {
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Report { out } => {
            if let Err(err) = write_report(&out, PathBuf::from("/app/data").as_path()) {
                eprintln!("{err}");
                std::process::exit(1);
            }
        }
    }
}
