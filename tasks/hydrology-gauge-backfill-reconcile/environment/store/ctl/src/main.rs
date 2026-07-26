mod subcmd_compact;
mod subcmd_query;

use std::fs;
use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};
use manifest::journal::JournalEntry;
use ops::workflow::{run_barrier, run_rebuild, run_roll, run_workflow};
use serde::Serialize;
use store::{RuntimeState, data_root, recovery_dir};
use subcmd_query::{run_query_aggregate, run_query_point, run_query_range};

#[derive(Parser)]
#[command(name = "ctl")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Roll {
        #[arg(long = "ks")]
        ks: String,
    },
    Barrier,
    Rebuild {
        #[arg(long = "ks")]
        ks: String,
    },
    Compact {
        #[arg(long = "ks")]
        ks: String,
    },
    Query {
        #[command(subcommand)]
        query: QueryCmd,
    },
    Report {
        #[arg(long = "out")]
        out: PathBuf,
    },
    Workflow {
        #[arg(long = "ks")]
        ks: String,
    },
    Status,
}

#[derive(Subcommand)]
enum QueryCmd {
    Point {
        #[arg(long = "ks")]
        ks: String,
        #[arg(long = "key")]
        key: String,
        #[arg(long = "ts")]
        ts: u64,
    },
    Range {
        #[arg(long = "ks")]
        ks: String,
        #[arg(long = "lo")]
        lo: String,
        #[arg(long = "hi")]
        hi: String,
        #[arg(long = "ts")]
        ts: u64,
    },
    Aggregate {
        #[arg(long = "ks")]
        ks: String,
        #[arg(long = "ts")]
        ts: u64,
    },
}

#[derive(Serialize)]
struct NamespaceReport {
    visible_segments: usize,
    sidecar_digest: String,
}

#[derive(Serialize)]
struct RewindReport {
    restored_generation: u64,
    #[serde(rename = "stations")]
    events: NamespaceReport,
    #[serde(rename = "telemetry")]
    metrics: NamespaceReport,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let root = data_root();
    let cfg = recovery_dir();

    match cli.command {
        Commands::Roll { ks } => run_roll(&root, &cfg, &ks)?,
        Commands::Barrier => run_barrier(&root, &cfg)?,
        Commands::Rebuild { ks } => run_rebuild(&root, &ks)?,
        Commands::Compact { ks } => subcmd_compact::run_compact(&root, &ks)?,
        Commands::Query { query } => match query {
            QueryCmd::Point { ks, key, ts } => {
                println!("{}", run_query_point(&root, &ks, &key, ts)?)
            }
            QueryCmd::Range { ks, lo, hi, ts } => {
                println!("{}", run_query_range(&root, &ks, &lo, &hi, ts)?)
            }
            QueryCmd::Aggregate { ks, ts } => println!("{}", run_query_aggregate(&root, &ks, ts)?),
        },
        Commands::Report { out } => {
            let runtime = RuntimeState::load(&root)?;
            let policy = ops::trust::TrustPolicy::load()?;
            ops::trust::assert_lineage_clean(
                &root,
                &policy.primary_channel,
                runtime.active_gen,
                policy.forbid_merged_stripe,
            )?;
            if policy.require_revocation_ledger {
                ops::revocation::assert_ledger_covers(&root, &runtime.tombstone_keys)?;
            }
            let events_sc = index::sidecar::load(&root, "events")?;
            let metrics_sc = index::sidecar::load(&root, "metrics")?;
            for key in &runtime.tombstone_keys {
                if events_sc.map.contains_key(key) {
                    anyhow::bail!("events sidecar still maps revoked key {key}");
                }
            }
            if events_sc.bound_gen != runtime.active_gen {
                anyhow::bail!(
                    "events sidecar bound_gen {} != active_gen {}",
                    events_sc.bound_gen,
                    runtime.active_gen
                );
            }
            let events_segments = JournalEntry::stripes_at(&root, "events", runtime.active_gen)?.len();
            let metrics_segments =
                JournalEntry::stripes_at(&root, "metrics", runtime.active_gen)?.len();
            let report = RewindReport {
                restored_generation: runtime.active_gen,
                events: NamespaceReport {
                    visible_segments: events_segments,
                    sidecar_digest: events_sc.digest,
                },
                metrics: NamespaceReport {
                    visible_segments: metrics_segments,
                    sidecar_digest: metrics_sc.digest,
                },
            };
            if let Some(parent) = out.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::write(&out, serde_json::to_string_pretty(&report)?)?;
            println!("wrote {}", out.display());
        }
        Commands::Status => {
            let runtime = RuntimeState::load(&root)?;
            let head = if runtime.ceiling_gen > 0 {
                runtime.ceiling_gen
            } else {
                runtime.active_gen
            };
            println!(
                "{}",
                serde_json::json!({
                    "active_gen": runtime.active_gen,
                    "ceiling_gen": head,
                    "wal_seq": runtime.wal_seq,
                })
            );
        }
        Commands::Workflow { ks } => run_workflow(&root, &cfg, &ks)?,
    }
    Ok(())
}
