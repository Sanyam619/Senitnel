use serde::Serialize;
use std::env;
use std::fs;
use std::path::PathBuf;
use verifycore::op_ring::threshold_at;
use verifycore::{
    active_ring, choose_head, load_ceremony, load_cosigners, load_events, load_shards, load_state,
    merge_attests, Event, HeadResolution, Ledger, ReconcileOutcome, ShardBook, ACCEPT_REASONS,
    REASON_CROSS_SHARD, REASON_STALE_HEAD, REJECT_REASONS,
};

#[derive(Serialize)]
struct VerdictRow {
    event_id: String,
    decision: String,
    reason: String,
}

#[derive(Serialize)]
struct Report {
    schema_version: u32,
    checkpoint_head: u64,
    events: Vec<VerdictRow>,
}

fn checkpoint_head(shards: &ShardBook) -> u64 {
    let mut m: u64 = 0;
    for s in shards.by_id.values() {
        for c in &s.checkpoints {
            if c.epoch > m {
                m = c.epoch;
            }
        }
    }
    m
}

fn evaluate(
    event: &Event,
    shards: &ShardBook,
    led: &Ledger,
    cos: &verifycore::CosignerBook,
) -> VerdictRow {
    match choose_head(shards, event) {
        HeadResolution::Missing => {
            return VerdictRow {
                event_id: event.event_id.clone(),
                decision: "reject".to_string(),
                reason: REASON_STALE_HEAD.to_string(),
            };
        }
        HeadResolution::Unattested => {
            return VerdictRow {
                event_id: event.event_id.clone(),
                decision: "reject".to_string(),
                reason: REASON_CROSS_SHARD.to_string(),
            };
        }
        HeadResolution::Bound(_) => {}
    }
    let led_c = led.clone();
    let cos_c = cos.clone();
    let ring_at = move |ep: u64| active_ring(&led_c, &cos_c, ep);
    let now = cos.now_epoch;
    let threshold = threshold_at(led, now);
    let outcome = merge_attests(event, led, cos, ring_at, threshold);
    match outcome {
        ReconcileOutcome::Accept { reason } => VerdictRow {
            event_id: event.event_id.clone(),
            decision: "accept".to_string(),
            reason: reason.to_string(),
        },
        ReconcileOutcome::Reject { reason } => VerdictRow {
            event_id: event.event_id.clone(),
            decision: "reject".to_string(),
            reason: reason.to_string(),
        },
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let cmd = args.get(1).map(|s| s.as_str()).unwrap_or("verify");
    let data_root = PathBuf::from(
        env::var("DATA_ROOT").unwrap_or_else(|_| "/data".to_string()),
    );
    let out_path = PathBuf::from(
        env::var("OUT_PATH").unwrap_or_else(|_| "/output/verdicts.json".to_string()),
    );

    match cmd {
        "verify" => {
            let _state = load_state(&data_root);
            let led = load_ceremony(&data_root);
            let cos = load_cosigners(&data_root);
            let shards = load_shards(&data_root);
            let events = load_events(&data_root);
            let head = checkpoint_head(&shards);

            let mut rows: Vec<VerdictRow> = Vec::new();
            for ev in &events {
                rows.push(evaluate(ev, &shards, &led, &cos));
            }
            rows.sort_by(|a, b| a.event_id.cmp(&b.event_id));

            for row in &rows {
                let ok_accept = row.decision == "accept"
                    && ACCEPT_REASONS.iter().any(|r| *r == row.reason.as_str());
                let ok_reject = row.decision == "reject"
                    && REJECT_REASONS.iter().any(|r| *r == row.reason.as_str());
                assert!(
                    ok_accept || ok_reject,
                    "reason not in enum: {:?}",
                    row.reason
                );
            }

            let report = Report {
                schema_version: 1,
                checkpoint_head: head,
                events: rows,
            };
            fs::create_dir_all(out_path.parent().unwrap_or(std::path::Path::new("/"))).ok();
            let s = serde_json::to_string_pretty(&report).expect("serialize");
            fs::write(&out_path, s + "\n").expect("write verdicts");
        }
        "status" => {
            let shards = load_shards(&data_root);
            let events = load_events(&data_root);
            println!(
                "shards={} events={} head={}",
                shards.by_id.len(),
                events.len(),
                checkpoint_head(&shards)
            );
        }
        _ => {
            eprintln!("usage: vfy verify|status");
            std::process::exit(2);
        }
    }
}
