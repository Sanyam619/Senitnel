# Idea seed — Battery Pack Thermal Conservation Gate

**Idea Category:** Scientific Computing

**Languages (authoring):** python, bash

## Task Idea Summary

Operate the existing lithium-ion pack thermal evaluation desk under /app (finite-volume thermal solver, contact resistance modules, profiles, and report harness already installed) so rebuilt solves from /app meet the energy-conservation and hotspot agreement bands in /app/docs/thermal_bands.md on frozen pack fixtures under /app/data/packs/ (ledger /app/data/packs/LEDGER.sha256; do not alter fixtures). Emit /output/thermal-conserve-report.json only by running /app/ops/run_thermal_report.sh --all-profiles after rebuild. Report schema: status (string, "ok"), eval_sha (string), profiles (array of objects with profile_id string, energy_rel_err number, hotspot_rel_err number, max_dT_K number, contact_model string, reduction_order string, dt_policy string), and run_stamp (string). For ship and fleet profiles, /app/docs/thermal_bands.md publishes max_energy_rel_err, max_hotspot_rel_err, max_dT_K, and required contact_model, reduction_order, and dt_policy tokens from /app/config/profiles/*.toml; graded rules are energy_rel_err <= max_energy_rel_err, hotspot_rel_err <= max_hotspot_rel_err, max_dT_K <= the published cap, and the three policy tokens equal to the profile declarations. Both profiles must pass in one report. /app/bin/thermalsurf is a non-graded dashboard only. Verifier rebuilds from /app, re-runs the entrypoint, and requires byte-identical output across two consecutive runs.

## Associated Skills

pack thermal finite-volume solves; energy conservation residuals; hotspot temperature agreement; contact resistance models; reduction ordering; profile-declared time policies; automotive release bands; deterministic thermal reports

## Task Tags

thermal, battery, conservation, hotspot, residuals

## Category note

Numerical conservation/agreement bands for an engineering solver — `scientific-computing` (goal-first operate-the-desk, not a debugging/repair checklist).
