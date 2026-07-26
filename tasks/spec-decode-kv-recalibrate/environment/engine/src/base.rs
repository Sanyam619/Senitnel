//! Shared types, math, deterministic PRNG, and minimal JSON config parsing
//! used by the speculative-decoding evaluation pipeline.

use std::fs;
use std::path::Path;

/// Deterministic linear-congruential-derived PRNG. Given a fixed `seed` and
/// distinct `nonce` values, produces reproducible f64 in [0.0, 1.0).
pub fn prng(seed: u64, nonce: u64) -> f64 {
    let mut x = seed
        .wrapping_mul(6364136223846793005)
        .wrapping_add(nonce.wrapping_mul(1442695040888963407));
    x = x
        .wrapping_mul(6364136223846793005)
        .wrapping_add(1442695040888963407);
    x ^= x >> 33;
    x = x.wrapping_mul(0xff51afd7ed558ccd);
    x ^= x >> 33;
    x = x.wrapping_mul(0xc4ceb9fe1a85ec53);
    x ^= x >> 33;
    let bits = (x >> 11) as f64;
    bits / ((1u64 << 53) as f64)
}

/// Numerically stable softmax.
pub fn softmax(xs: &[f64]) -> Vec<f64> {
    let m = xs.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let exps: Vec<f64> = xs.iter().map(|x| (x - m).exp()).collect();
    let z: f64 = exps.iter().sum();
    exps.iter().map(|e| e / z).collect()
}

/// argmax returning the smallest index on ties.
pub fn argmax(xs: &[f64]) -> usize {
    let mut best = 0usize;
    for (i, x) in xs.iter().enumerate() {
        if *x > xs[best] {
            best = i;
        }
    }
    best
}

/// Sample from a discrete distribution via inverse-CDF given u in [0,1).
pub fn sample_cdf(probs: &[f64], u: f64) -> usize {
    let mut acc = 0.0f64;
    for (i, p) in probs.iter().enumerate() {
        acc += *p;
        if u < acc {
            return i;
        }
    }
    probs.len() - 1
}

/// Shannon entropy of a distribution, normalised into [0.0, 1.0].
pub fn entropy_normalised(probs: &[f64]) -> f64 {
    let mut h = 0.0f64;
    for &p in probs {
        if p > 0.0 {
            h -= p * p.ln();
        }
    }
    let max_h = (probs.len() as f64).ln();
    if max_h > 0.0 {
        (h / max_h).clamp(0.0, 1.0)
    } else {
        0.0
    }
}

/// A single decode position parsed from a slice fixture file.
#[derive(Clone)]
pub struct PositionRecord {
    pub layer_id: u32,
    pub entropy: f64,
    pub rare_flag: u32,
    pub target_logits: Vec<f64>,
    pub draft_logits: Vec<f64>,
}

/// A slice of positions.
#[derive(Clone)]
pub struct Slice {
    pub id: String,
    pub vocab: usize,
    pub positions: Vec<PositionRecord>,
}

/// Load a slice fixture file. First line is "V K", followed by K lines each
/// containing: layer_id entropy rare_flag t0 t1 ... t{V-1} d0 d1 ... d{V-1}
pub fn load_slice(id: &str, path: &Path) -> Slice {
    let text = fs::read_to_string(path)
        .unwrap_or_else(|e| panic!("cannot read slice fixture {}: {}", path.display(), e));
    let mut lines = text.lines();
    let header = lines.next().expect("slice fixture missing header");
    let mut hdr = header.split_whitespace();
    let vocab: usize = hdr.next().unwrap().parse().unwrap();
    let k: usize = hdr.next().unwrap().parse().unwrap();
    let mut positions = Vec::with_capacity(k);
    for (i, line) in lines.enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let mut it = line.split_whitespace();
        let layer_id: u32 = it.next().unwrap().parse().unwrap();
        let entropy: f64 = it.next().unwrap().parse().unwrap();
        let rare_flag: u32 = it.next().unwrap().parse().unwrap();
        let mut target = Vec::with_capacity(vocab);
        for _ in 0..vocab {
            target.push(it.next().unwrap().parse().unwrap());
        }
        let mut draft = Vec::with_capacity(vocab);
        for _ in 0..vocab {
            draft.push(it.next().unwrap().parse().unwrap());
        }
        positions.push(PositionRecord {
            layer_id,
            entropy,
            rare_flag,
            target_logits: target,
            draft_logits: draft,
        });
        if positions.len() >= k {
            break;
        }
        let _ = i;
    }
    Slice { id: id.to_string(), vocab, positions }
}

/// Load reference token ids (one per line).
pub fn load_reference(path: &Path) -> Vec<usize> {
    let text = fs::read_to_string(path)
        .unwrap_or_else(|e| panic!("cannot read reference {}: {}", path.display(), e));
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| l.trim().parse().unwrap())
        .collect()
}

/// Minimal JSON support: extract the numeric value or numeric array for a
/// given top-level key. Not a general parser; assumes well-formed input
/// produced by our own fixture generator.
pub fn json_number(text: &str, key: &str) -> Option<f64> {
    let needle = format!("\"{}\"", key);
    let idx = text.find(&needle)?;
    let after = &text[idx + needle.len()..];
    let colon = after.find(':')?;
    let rest = &after[colon + 1..];
    let mut buf = String::new();
    for ch in rest.chars() {
        if ch == '-' || ch == '.' || ch == 'e' || ch == 'E' || ch.is_ascii_digit() {
            buf.push(ch);
        } else if buf.is_empty() && (ch.is_whitespace() || ch == '+') {
            continue;
        } else {
            break;
        }
    }
    buf.parse().ok()
}

pub fn json_number_array(text: &str, key: &str) -> Option<Vec<f64>> {
    let needle = format!("\"{}\"", key);
    let idx = text.find(&needle)?;
    let after = &text[idx + needle.len()..];
    let lb = after.find('[')?;
    let rb = after.find(']')?;
    let inner = &after[lb + 1..rb];
    let mut out = Vec::new();
    for tok in inner.split(',') {
        let t = tok.trim();
        if t.is_empty() {
            continue;
        }
        out.push(t.parse().ok()?);
    }
    Some(out)
}

/// Emit a JSON number that plays well with our tolerances: 6 fractional digits.
pub fn fnum(x: f64) -> String {
    format!("{:.6}", x)
}

/// Emit a JSON integer.
pub fn inum(x: i64) -> String {
    format!("{}", x)
}

/// A per-slice metric record.
#[derive(Clone)]
pub struct SliceMetrics {
    pub slice_id: String,
    pub positions: usize,
    pub ks_statistic: f64,
    pub accept_rate: f64,
    pub divergence_rate: f64,
    pub speedup: f64,
    pub fallback_rate: f64,
    pub low_entropy_accept_rate: f64,
    pub high_entropy_accept_rate: f64,
    /// Mean total-variation distance between the calibrated draft
    /// distribution and the target distribution across positions.
    pub mean_draft_target_tv: f64,
}

/// A per-position event emitted by the runner for anti-tamper verification.
#[derive(Clone)]
pub struct PositionEvent {
    pub slice_id: String,
    pub pos: usize,
    pub emitted: usize,
    pub reference: usize,
    pub accepted: u32,
    pub fallback: u32,
    pub entropy: f64,
    pub rare_flag: u32,
    /// Total-variation distance between calibrated draft and target at
    /// this position: `0.5 * sum_i |p_target[i] - p_draft[i]|`.
    pub draft_target_tv: f64,
}
