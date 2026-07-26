use std::env;
use std::fs;
use std::process;

use ed25519_dalek::{Signature, SigningKey, Verifier};
use sha2::{Digest, Sha256};

const SIG_LEN: usize = 64;
const DOMAIN: &[u8] = b"SHSM";
const KEY_DOM: &[u8] = b"shsm.v1\0";

fn main() {
    let mut args = env::args().skip(1);
    let mut frame_path = None;
    while let Some(a) = args.next() {
        if a == "--frame" {
            frame_path = args.next();
        }
    }
    let Some(path) = frame_path else {
        eprintln!("usage: framecheck --frame <path>");
        process::exit(2);
    };
    let Ok(raw) = fs::read(&path) else {
        eprintln!("unreadable frame");
        process::exit(1);
    };
    if raw.len() < 6 + SIG_LEN || raw[0] != 0xA5 {
        eprintln!("bad frame");
        process::exit(1);
    }
    let lane_id = raw[1];
    let epoch = u16::from_be_bytes([raw[2], raw[3]]);
    let plen = u16::from_be_bytes([raw[4], raw[5]]) as usize;
    if 6 + plen + SIG_LEN > raw.len() {
        eprintln!("truncated frame");
        process::exit(1);
    }
    let payload = &raw[6..6 + plen];
    let sig = &raw[6 + plen..6 + plen + SIG_LEN];

    // Seed from manifest tip for this epoch when available; else audit seed.
    let seed = load_seed(epoch).unwrap_or_else(|| hex_decode("c3a7f1b8"));
    let sk = derive_sk(&seed, epoch);
    let mut msg = Vec::with_capacity(4 + 2 + 1 + payload.len());
    msg.extend_from_slice(DOMAIN);
    msg.extend_from_slice(&epoch.to_be_bytes());
    msg.push(lane_id);
    msg.extend_from_slice(payload);

    let sk_bytes: [u8; 32] = match sk.as_slice().try_into() {
        Ok(b) => b,
        Err(_) => {
            eprintln!("bad key");
            process::exit(1);
        }
    };
    let sig_bytes: [u8; 64] = match sig.try_into() {
        Ok(b) => b,
        Err(_) => {
            eprintln!("bad sig");
            process::exit(1);
        }
    };
    let signing = SigningKey::from_bytes(&sk_bytes);
    let vk = signing.verifying_key();
    let signature = Signature::from_bytes(&sig_bytes);
    if vk.verify_strict(&msg, &signature).is_ok() {
        println!("ok");
        process::exit(0);
    }
    eprintln!("mismatch");
    process::exit(1);
}

fn derive_sk(seed: &[u8], epoch: u16) -> Vec<u8> {
    let mut h = Sha256::new();
    h.update(KEY_DOM);
    h.update(seed);
    h.update(&epoch.to_be_bytes());
    h.finalize().to_vec()
}

fn load_seed(epoch: u16) -> Option<Vec<u8>> {
    let path = "/app/data/manifests/tier_intermediate.jsonl";
    let text = fs::read_to_string(path).ok()?;
    for line in text.lines() {
        if !line.contains(&format!("\"epoch\":{epoch}")) && !line.contains(&format!("\"epoch\": {epoch}"))
        {
            continue;
        }
        if let Some(seed) = extract_json_str(line, "\"seed\":") {
            return Some(hex_decode(&seed));
        }
    }
    None
}

fn extract_json_str(line: &str, key: &str) -> Option<String> {
    let i = line.find(key)?;
    let rest = &line[i + key.len()..];
    let start = rest.find('"')? + 1;
    let end = start + rest[start..].find('"')?;
    Some(rest[start..end].to_string())
}

fn hex_decode(hex: &str) -> Vec<u8> {
    let mut out = Vec::new();
    let mut chars = hex.chars();
    while let (Some(a), Some(b)) = (chars.next(), chars.next()) {
        if let (Some(hi), Some(lo)) = (a.to_digit(16), b.to_digit(16)) {
            out.push((hi * 16 + lo) as u8);
        }
    }
    out
}
