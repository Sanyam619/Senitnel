# Thermal release bands

Frozen pack fixtures under `/app/data/packs/` are integrity-ledger protected via `/app/data/packs/LEDGER.sha256` (do not alter fixture bytes).

For each profile in `/app/config/profiles/`:

- `max_energy_rel_err` = 1e-9
- `max_hotspot_rel_err` = 1e-6
- `max_dT_K` = 1e-4

Required tokens are the profile's `contact_model`, `reduction_order`, and `dt_policy` fields. Graded report rows must echo those profile declarations.

Fleet-trial preference material under `/app/data/policy/trial_pref.live` must not stay authoritative once the cross-profile handoff is accepted. Accepted handoff means `/app/data/policy/handoff.accept` is present and `/app/data/policy/trial_pref.live` is absent. Evaluation prep must not recreate the trial preference while the accept receipt remains.

Energy conservation is judged on relative drift `|E1 - E0| / max(|E0|, eps)` after the finite-volume advance. Hotspot agreement compares solved cell temperatures to the frozen reference packs under `/app/data/refs/` for the active profile.

The graded report is emitted by `/app/scripts/run_thermal_eval.sh`. `/app/bin/thermalsurf` is observational only and does not certify conservation.
