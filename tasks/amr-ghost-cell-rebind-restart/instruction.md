Restarting against a newer archived layout leaves `recover-all` at exit zero while face-adjacent layer norms in `/output/restart-summary.json` still disagree with the frozen reference slices under `/app/data/ref_slices/`; interior sampling looks fine.

Bring every bundled fixture under `/app/data/fixtures/` back to layout-consistent state through the recovery entrypoint. Emit `/output/restart-summary.json` with top-level schema_tag, scenarios, mass_drift, and tree_depth. mass_drift and tree_depth belong at the root only, not inside scenario rows. Each scenarios entry must contain exactly label, block_tally, and face_l2.

Also write field dumps at `/output/fields/alpha/t0.bin`, `/output/fields/alpha/t1.bin`, `/output/fields/beta/t0.bin`, `/output/fields/beta/t1.bin`, `/output/fields/gamma/t0.bin`, and `/output/fields/gamma/t1.bin`. The first eight bytes of each dump are two little-endian float32 values in this order: face_l2, then mass_drift. For a given label, the t1 face_l2 value must not exceed the t0 face_l2 value by more than 1e-5.

Face-layer error and mass drift must stay within the restart validation constants in `/app/include/forge.h`. Block tallies and tree_depth must match the scenario sections of `/app/data/policy_v2.table`.

Rebuild after source edits, then run `/app/scripts/run_restart.sh`.
