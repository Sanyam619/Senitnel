# Preference-Model KL-Constrained Policy Eval — Authoring Brief

## Metadata

- **Task name:** `preference-model-kl-constrained-eval`
- **Category:** `machine-learning` (alignment / preference eval against win-rate × KL bands)
- **Languages:** `rust`, `bash`
- **Difficulty:** hard
- **Codebase size:** small

## Goal (solver-visible)

Seat the preference-alignment eval desk so `/app/scripts/run_pref_eval.sh` emits
`/output/pref-eval.json` with `schema_tag`, `slices[]` (`id`, `win_rate`,
`kl_to_ref`, `beta`, `tip_epoch`), and `eval_ok`. Frozen prefs / ref / policy
under `/app/data/`. Each required slice in `/app/docs/pref_bands.md` must meet
its win-rate band while `kl_to_ref` stays ≤ the published ceiling; `beta` equals
the durable tip beta; `tip_epoch` equals the sealed journal tip (not the live
high-beta tip). `/app/tools/prefprobe` may report high win_rate while `eval_ok`
is false. Verifier rebuilds `/app/eng` and re-runs; two runs byte-identical.

## Hardness design

SoftHSM-class `calib/trial_pref.toml` (`selection=trial|serving`) ×
`calib/tip_bind.accept` matching journal-resolved durable tip. `eng/build.rs`
rematerializes five seating surfaces from seeds until the gate passes.

### Tip resolution

Sealed ∧ not in `retired_tips.jsonl` ∧ max epoch → `tip_g7` (epoch 4, beta 0.20).
Baits: `tip_g9` sealed-max but retired; `tip_live` unsealed high-beta 1.80;
`live.toml` / `durable.toml` mirrors.

### Flipping-point loci (≥3)

| Location | Controls |
| -------- | -------- |
| `seat/knit_b.rs` tip pick | tip_epoch / beta source cells |
| `flag/xv_c.rs` beta seat | beta field vs live mirror |
| `mix/ward_d.rs` win scoring | soft sigmoid(beta·margin) win_rate |
| `score/helm_e.rs` KL | mean KL(cand‖ref) |
| `gate/emit_f.rs` eval_ok | bands ∧ KL ceilings ∧ tip match |

Ship correct thin pipes + `base.rs` I/O. Broken seeds: newest-any tip; live beta;
always-win; zero KL; win-only gate (prefprobe-class).

### Why not repair/debug / SE

Instruction leads with preference-model eval outcomes (win-rate × KL × tip).
Tags: preference-model, kl-constraint, win-rate, beta-tip, tip-epoch,
inference-eval. Layout uses `calib/` + evaluation selection, not ops/cutover.

## Construction manifest (symbol table)

| Symbol | Path | Role |
| ------ | ---- | ---- |
| `pick_t` | `seat/knit_b.rs` | tip epoch + beta from journal |
| `bit_z` | `flag/xv_c.rs` | seat reported beta |
| `mix_w` | `mix/ward_d.rs` | soft win_rate |
| `score_u` | `score/helm_e.rs` | KL to reference |
| `gate_y` | `gate/emit_f.rs` | deep eval_ok |

`code_forbidden_tokens` (fix-path): preference, win_rate, kl_to_ref, beta_tip,
tip_epoch, eval_ok, ceiling, band, sigmoid, rematerialize, serving.

## Discovery budget (≥3)

1. Tip = sealed-max minus retired (not live high-beta) — journal + retired files.
2. Soft win uses tip beta as scale — margins alone ≠ reported win_rate under wrong beta.
3. `eval_ok` requires KL ceilings + tip fields; prefprobe win-only is false-green.
4. Trial selection rematerializes all five surfaces until serving + matching bind.

## Tests (hard cells)

Schema/bands; tip ≠ live/retired; beta = durable tip; KL ≤ ceilings; win bands;
eval_ok true; prefprobe not authoritative; fixture integrity; rebuild re-entry;
byte-identical; novel tip inject; novel slice inject; surface_ok anti-copy.
