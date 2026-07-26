use std::collections::HashMap;

use crate::emit_c::QuarantineEntry;
use crate::skim_fold::Frame;

pub fn decode_wal_with_reject_ledger(
    raw: &[u8],
    nonces: &HashMap<u16, Vec<u8>>,
) -> (Vec<Frame>, Vec<QuarantineEntry>) {
    let lane_names: HashMap<u8, &str> = [
        (1, "mqtt"),
        (2, "lora"),
        (3, "uart"),
        (4, "canbus"),
        (5, "zigbee"),
    ]
    .into_iter()
    .collect();

    let mut accepted = Vec::new();
    let mut rejected = Vec::new();
    let mut i = 0usize;

    while i + 6 <= raw.len() {
        if raw[i] != 0xA5 {
            i += 1;
            continue;
        }
        let lane_id = raw[i + 1];
        let epoch = u16::from_be_bytes([raw[i + 2], raw[i + 3]]);
        let plen = u16::from_be_bytes([raw[i + 4], raw[i + 5]]) as usize;
        let start = i + 6;
        let end = start + plen;
        if end + 1 > raw.len() {
            break;
        }
        let payload = &raw[start..end];
        let stored_integrity = raw[end];

        let text = String::from_utf8_lossy(payload);
        let ts = parse_ts(&text).unwrap_or(0);
        let hold = text.contains("hold=1");
        let lane_name = lane_names.get(&lane_id).unwrap_or(&"unknown");

        let valid = verify_frame(payload, stored_integrity, epoch, nonces);

        if valid {
            accepted.push(Frame {
                epoch,
                lane: lane_name.to_string(),
                ts,
                hold,
                from_wal: true,
            });
        } else {
            rejected.push(QuarantineEntry {
                epoch,
                lane: lane_name.to_string(),
                ts,
                reason: "seal_break".to_string(),
            });
        }

        i = end + 1;
    }
    (accepted, rejected)
}

fn verify_frame(
    payload: &[u8],
    stored: u8,
    epoch: u16,
    nonces: &HashMap<u16, Vec<u8>>,
) -> bool {
    let nonce = match nonces.get(&epoch) {
        Some(n) => n,
        None => return true,
    };
    if nonce.is_empty() || nonce.iter().all(|&b| b == 0) {
        return true;
    }
    let computed: u8 = payload.iter().fold(0u8, |acc, &b| acc.wrapping_add(b));
    computed == stored
}

fn parse_ts(text: &str) -> Option<u64> {
    let i = text.find("ts=")?;
    let rest = &text[i + 3..];
    let digits: String = rest.chars().take_while(|c| c.is_ascii_digit()).collect();
    digits.parse().ok()
}
