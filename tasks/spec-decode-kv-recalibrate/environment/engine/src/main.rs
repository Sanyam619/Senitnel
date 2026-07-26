//! spec-eval: speculative-decoding evaluation harness.
//!
//! Subcommands:
//!   spec-eval eval  --out /path/to/report.json [--seed N]
//!   spec-eval probe --slice <name> --out /path/to/events.jsonl [--seed N]
//!
//! Reads slice fixtures under /app/data/slices and nonspec token streams
//! under /app/data/nonspec. Runs the speculative decoder for each
//! position and emits per-slice metrics.

mod base;
mod axis;
mod warden;
mod helm;
mod pipeline;

use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use crate::base::{
    argmax, fnum, inum, json_number, json_number_array, load_reference, load_slice, prng, softmax,
    PositionEvent, PositionRecord, Slice, SliceMetrics,
};
use crate::axis::{stage_a_transform, StageAConfig};
use crate::warden::{stage_b_admit, StageBConfig};
use crate::helm::{stage_c_route, Decision, StageCConfig};
use crate::pipeline::{select_proposal_token, compute_position_tv, acceptance_target_probability};

const SLICES: &[&str] = &[
    "num_completion",
    "repetition_prose",
    "low_entropy_json",
    "code_rare_tokens",
];

const DEFAULT_SEED: u64 = 0xC0FFEE_u64;
const DATA_ROOT: &str = "/app/data";

struct Contexts {
    axis: StageAConfig,
    warden: StageBConfig,
    helm: StageCConfig,
}

fn load_contexts(cfg_root: &Path) -> Contexts {
    let scales_txt = fs::read_to_string(cfg_root.join("layer_scales.json"))
        .expect("layer_scales.json missing");
    let scales = json_number_array(&scales_txt, "scales").expect("scales array");

    let blocks_txt = fs::read_to_string(cfg_root.join("quant_blocks.json"))
        .expect("quant_blocks.json missing");
    let block_size = json_number(&blocks_txt, "block_size").expect("block_size") as usize;
    let block_bias =
        json_number_array(&blocks_txt, "block_bias").expect("block_bias array");

    let codebook_txt = fs::read_to_string(cfg_root.join("codebook_stats.json"))
        .expect("codebook_stats.json missing");
    let low_entropy_threshold =
        json_number(&codebook_txt, "low_entropy_threshold").expect("low_entropy_threshold");
    let l1_error_low_entropy =
        json_number(&codebook_txt, "l1_error_low_entropy").expect("l1_error_low_entropy");

    let sched_txt = fs::read_to_string(cfg_root.join("params.json"))
        .expect("params.json missing");
    let recent_window = json_number(&sched_txt, "recent_window").expect("recent_window") as usize;
    let accept_floor = json_number(&sched_txt, "accept_floor").expect("accept_floor");

    Contexts {
        axis: StageAConfig {
            layer_scales: scales,
            block_size,
            block_bias,
            low_entropy_threshold,
        },
        warden: StageBConfig {
            low_entropy_threshold,
            l1_error_low_entropy,
        },
        helm: StageCConfig {
            recent_window,
            accept_floor,
            low_entropy_threshold,
        },
    }
}

fn residual_sample(target: &[f64], draft: &[f64], u: f64) -> (usize, f64) {
    let mut r: Vec<f64> = target
        .iter()
        .zip(draft.iter())
        .map(|(t, d)| (t - d).max(0.0))
        .collect();
    let z: f64 = r.iter().sum();
    let idx = if z > 1e-6 {
        for x in r.iter_mut() {
            *x /= z;
        }
        argmax(&r)
    } else {
        argmax(draft)
    };
    let _ = u;
    (idx, z)
}

fn nonce_for(slice_id: &str, pos: usize, tag: u64) -> u64 {
    let mut h = 1469598103934665603u64;
    for b in slice_id.as_bytes() {
        h ^= *b as u64;
        h = h.wrapping_mul(1099511628211);
    }
    h = h.wrapping_add(pos as u64);
    h = h.wrapping_mul(6364136223846793005);
    h = h.wrapping_add(tag);
    h
}

struct SlicePass {
    metrics: SliceMetrics,
    events: Vec<PositionEvent>,
    generated: Vec<usize>,
}

fn evaluate_slice(slice: &Slice, reference: &[usize], seed: u64, ctxs: &Contexts) -> SlicePass {
    let mut generated = Vec::with_capacity(slice.positions.len());
    let mut events = Vec::with_capacity(slice.positions.len());
    let mut accepts = 0usize;
    let mut rejects = 0usize;
    let mut fallbacks = 0usize;
    let mut divergences = 0usize;
    let mut low_entropy_accepts = 0usize;
    let mut low_entropy_positions = 0usize;
    let mut high_entropy_accepts = 0usize;
    let mut high_entropy_positions = 0usize;
    let mut tv_sum = 0.0f64;
    let mut recent_bits: Vec<u32> = Vec::with_capacity(ctxs.helm.recent_window);

    for (pos, rec) in slice.positions.iter().enumerate() {
        let target_dist = softmax(&rec.target_logits);
        let calibrated = stage_a_transform(rec, &ctxs.axis);
        let draft_dist = softmax(&calibrated);
        let draft_target_tv = compute_position_tv(&target_dist, rec, &draft_dist);
        tv_sum += draft_target_tv;

        let draft_token = select_proposal_token(rec, &draft_dist);

        let p_d = draft_dist[draft_token];
        let p_t = acceptance_target_probability(&target_dist, draft_token);
        let accept_prob = stage_b_admit(p_d, p_t, rec.entropy, &ctxs.warden);
        let u_accept = prng(seed, nonce_for(&slice.id, pos, 1));

        let recent_rate = if recent_bits.is_empty() {
            1.0
        } else {
            let s: u32 = recent_bits.iter().sum();
            s as f64 / recent_bits.len() as f64
        };

        let (emitted, accepted_bit, fallback_bit) = if u_accept <= accept_prob {
            (draft_token, 1u32, 0u32)
        } else {
            let dec = stage_c_route(recent_rate, rec.entropy, rec.rare_flag == 1, &ctxs.helm);
            match dec {
                Decision::Residual => {
                    let mut r: Vec<f64> = target_dist
                        .iter()
                        .zip(draft_dist.iter())
                        .map(|(t, d)| (t - d).max(0.0))
                        .collect();
                    let z: f64 = r.iter().sum();
                    let tok = if z > 1e-6 {
                        for x in r.iter_mut() {
                            *x /= z;
                        }
                        argmax(&r)
                    } else {
                        argmax(&draft_dist)
                    };
                    (tok, 0u32, 0u32)
                }
                Decision::Fallback => (argmax(&target_dist), 0u32, 1u32),
            }
        };

        recent_bits.push(accepted_bit);
        if recent_bits.len() > ctxs.helm.recent_window {
            recent_bits.remove(0);
        }

        if accepted_bit == 1 {
            accepts += 1;
        } else if fallback_bit == 1 {
            fallbacks += 1;
        } else {
            rejects += 1;
        }

        let reference_tok = reference[pos];
        if emitted != reference_tok {
            divergences += 1;
        }

        let tgt_ent = rec.entropy;
        if tgt_ent < ctxs.axis.low_entropy_threshold {
            low_entropy_positions += 1;
            if accepted_bit == 1 {
                low_entropy_accepts += 1;
            }
        } else {
            high_entropy_positions += 1;
            if accepted_bit == 1 {
                high_entropy_accepts += 1;
            }
        }

        generated.push(emitted);
        events.push(PositionEvent {
            slice_id: slice.id.clone(),
            pos,
            emitted,
            reference: reference_tok,
            accepted: accepted_bit,
            fallback: fallback_bit,
            entropy: tgt_ent,
            rare_flag: rec.rare_flag,
            draft_target_tv,
        });
    }

    let total = slice.positions.len();
    let accept_rate = accepts as f64 / total as f64;
    let fallback_rate = fallbacks as f64 / total as f64;
    let divergence_rate = divergences as f64 / total as f64;
    let speedup = 1.0 + accept_rate;
    let mean_draft_target_tv = if total > 0 { tv_sum / total as f64 } else { 0.0 };

    let ks = ks_statistic(&generated, reference, slice.vocab);

    let low_rate = if low_entropy_positions > 0 {
        low_entropy_accepts as f64 / low_entropy_positions as f64
    } else {
        0.0
    };
    let high_rate = if high_entropy_positions > 0 {
        high_entropy_accepts as f64 / high_entropy_positions as f64
    } else {
        0.0
    };

    let metrics = SliceMetrics {
        slice_id: slice.id.clone(),
        positions: total,
        ks_statistic: ks,
        accept_rate,
        divergence_rate,
        speedup,
        fallback_rate,
        low_entropy_accept_rate: low_rate,
        high_entropy_accept_rate: high_rate,
        mean_draft_target_tv,
    };
    let _ = rejects;
    SlicePass { metrics, events, generated }
}

fn ks_statistic(generated: &[usize], reference: &[usize], vocab: usize) -> f64 {
    let mut gen_hist = vec![0u64; vocab];
    let mut ref_hist = vec![0u64; vocab];
    for &t in generated {
        gen_hist[t] += 1;
    }
    for &t in reference {
        ref_hist[t] += 1;
    }
    let g_total = generated.len() as f64;
    let r_total = reference.len() as f64;
    let mut cum_g = 0.0f64;
    let mut cum_r = 0.0f64;
    let mut max_diff = 0.0f64;
    for i in 0..vocab {
        cum_g += gen_hist[i] as f64 / g_total;
        cum_r += ref_hist[i] as f64 / r_total;
        let d = (cum_g - cum_r).abs();
        if d > max_diff {
            max_diff = d;
        }
    }
    max_diff
}

fn load_all(data_root: &Path) -> Vec<(Slice, Vec<usize>)> {
    let mut out = Vec::new();
    for name in SLICES {
        let slice = load_slice(name, &data_root.join("slices").join(format!("{}.dat", name)));
        let refs = load_reference(&data_root.join("nonspec").join(format!("{}.dat", name)));
        out.push((slice, refs));
    }
    out
}

fn emit_report(passes: &[SlicePass], out_path: &Path, seed: u64) {
    let mut s = String::new();
    s.push_str("{\n");
    s.push_str("  \"schema_tag\": \"spec-calib-v1\",\n");
    s.push_str(&format!("  \"seed\": {},\n", seed));
    s.push_str("  \"slices\": [\n");
    for (i, p) in passes.iter().enumerate() {
        let m = &p.metrics;
        s.push_str("    {\n");
        s.push_str(&format!("      \"slice_id\": \"{}\",\n", m.slice_id));
        s.push_str(&format!("      \"positions\": {},\n", inum(m.positions as i64)));
        s.push_str(&format!("      \"ks_statistic\": {},\n", fnum(m.ks_statistic)));
        s.push_str(&format!("      \"accept_rate\": {},\n", fnum(m.accept_rate)));
        s.push_str(&format!("      \"divergence_rate\": {},\n", fnum(m.divergence_rate)));
        s.push_str(&format!("      \"speedup\": {},\n", fnum(m.speedup)));
        s.push_str(&format!("      \"fallback_rate\": {},\n", fnum(m.fallback_rate)));
        s.push_str(&format!(
            "      \"low_entropy_accept_rate\": {},\n",
            fnum(m.low_entropy_accept_rate)
        ));
        s.push_str(&format!(
            "      \"high_entropy_accept_rate\": {},\n",
            fnum(m.high_entropy_accept_rate)
        ));
        s.push_str(&format!(
            "      \"mean_draft_target_tv\": {}\n",
            fnum(m.mean_draft_target_tv)
        ));
        s.push_str("    }");
        if i + 1 < passes.len() {
            s.push(',');
        }
        s.push('\n');
    }
    s.push_str("  ],\n");

    let mut low_pos = 0u64;
    let mut low_acc = 0u64;
    let mut low_fb = 0u64;
    let mut high_pos = 0u64;
    let mut high_acc = 0u64;
    let mut high_fb = 0u64;
    let mut tot_pos = 0u64;
    let mut tot_acc = 0u64;
    let mut tot_fb = 0u64;
    let mut tot_div = 0u64;
    for p in passes {
        for ev in &p.events {
            tot_pos += 1;
            tot_acc += ev.accepted as u64;
            tot_fb += ev.fallback as u64;
            if ev.emitted != ev.reference {
                tot_div += 1;
            }
            if ev.entropy < 0.45 {
                low_pos += 1;
                low_acc += ev.accepted as u64;
                low_fb += ev.fallback as u64;
            } else {
                high_pos += 1;
                high_acc += ev.accepted as u64;
                high_fb += ev.fallback as u64;
            }
        }
    }
    let overall_accept = tot_acc as f64 / tot_pos as f64;
    let overall_divergence = tot_div as f64 / tot_pos as f64;
    let overall_fallback = tot_fb as f64 / tot_pos as f64;
    let overall_speedup = 1.0 + overall_accept;
    let all_pass = passes.iter().all(|p| {
        let m = &p.metrics;
        m.divergence_rate <= 0.05 && m.accept_rate >= 0.30 && m.ks_statistic <= 0.10
    });

    s.push_str("  \"positions\": {\n");
    s.push_str("    \"low_entropy\": {\n");
    s.push_str(&format!("      \"count\": {},\n", inum(low_pos as i64)));
    s.push_str(&format!(
        "      \"accept_rate\": {},\n",
        fnum(if low_pos > 0 { low_acc as f64 / low_pos as f64 } else { 0.0 })
    ));
    s.push_str(&format!(
        "      \"fallback_rate\": {}\n",
        fnum(if low_pos > 0 { low_fb as f64 / low_pos as f64 } else { 0.0 })
    ));
    s.push_str("    },\n");
    s.push_str("    \"high_entropy\": {\n");
    s.push_str(&format!("      \"count\": {},\n", inum(high_pos as i64)));
    s.push_str(&format!(
        "      \"accept_rate\": {},\n",
        fnum(if high_pos > 0 { high_acc as f64 / high_pos as f64 } else { 0.0 })
    ));
    s.push_str(&format!(
        "      \"fallback_rate\": {}\n",
        fnum(if high_pos > 0 { high_fb as f64 / high_pos as f64 } else { 0.0 })
    ));
    s.push_str("    }\n");
    s.push_str("  },\n");
    s.push_str("  \"summary\": {\n");
    s.push_str(&format!("    \"overall_speedup\": {},\n", fnum(overall_speedup)));
    s.push_str(&format!(
        "    \"overall_divergence\": {},\n",
        fnum(overall_divergence)
    ));
    s.push_str(&format!(
        "    \"overall_fallback_rate\": {},\n",
        fnum(overall_fallback)
    ));
    s.push_str(&format!(
        "    \"all_slices_pass\": {}\n",
        if all_pass { "true" } else { "false" }
    ));
    s.push_str("  }\n");
    s.push_str("}\n");
    fs::create_dir_all(out_path.parent().unwrap()).unwrap();
    fs::write(out_path, s).unwrap();
}

fn emit_events(passes: &[SlicePass], out_path: &Path) {
    let mut s = String::new();
    for p in passes {
        for ev in &p.events {
            s.push_str(&format!(
                "{{\"slice\":\"{}\",\"pos\":{},\"emitted\":{},\"reference\":{},\"accepted\":{},\"fallback\":{},\"entropy\":{},\"rare_flag\":{},\"draft_target_tv\":{}}}\n",
                ev.slice_id, ev.pos, ev.emitted, ev.reference,
                ev.accepted, ev.fallback, fnum(ev.entropy), ev.rare_flag,
                fnum(ev.draft_target_tv)
            ));
        }
    }
    fs::create_dir_all(out_path.parent().unwrap()).unwrap();
    fs::write(out_path, s).unwrap();
}

fn parse_flag<'a>(args: &'a [String], flag: &str) -> Option<&'a str> {
    let mut it = args.iter();
    while let Some(a) = it.next() {
        if a == flag {
            return it.next().map(|s| s.as_str());
        }
    }
    None
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        eprintln!("usage: spec-eval <eval|probe> [flags]");
        std::process::exit(2);
    }
    let cmd = args[0].clone();
    let rest = &args[1..];
    let seed = parse_flag(rest, "--seed")
        .and_then(|s| s.parse::<u64>().ok())
        .unwrap_or(DEFAULT_SEED);

    let data_root = PathBuf::from(
        parse_flag(rest, "--data").unwrap_or(DATA_ROOT),
    );
    let contexts = load_contexts(&data_root.join("config"));
    let all = load_all(&data_root);
    let mut passes = Vec::new();
    for (slice, refs) in &all {
        passes.push(evaluate_slice(slice, refs, seed, &contexts));
    }

    match cmd.as_str() {
        "eval" => {
            let out = PathBuf::from(
                parse_flag(rest, "--out").unwrap_or("/output/recalibration-report.json"),
            );
            emit_report(&passes, &out, seed);
            println!("wrote {}", out.display());
        }
        "probe" => {
            let out = PathBuf::from(
                parse_flag(rest, "--out").unwrap_or("/tmp/spec-eval-events.jsonl"),
            );
            if let Some(single) = parse_flag(rest, "--slice") {
                passes.retain(|p| p.metrics.slice_id == single);
            }
            emit_events(&passes, &out);
            println!("wrote {}", out.display());
        }
        other => {
            eprintln!("unknown subcommand: {}", other);
            std::process::exit(2);
        }
    }

    // silence unused-import warning for PositionRecord in the trivial case
    let _ = |p: &PositionRecord| p.layer_id;
}
