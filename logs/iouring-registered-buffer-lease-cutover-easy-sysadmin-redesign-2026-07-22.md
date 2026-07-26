# iouring-registered-buffer-lease-cutover — sysadmin redesign (2026-07-22)

## Feedback (artifact 11 + human review)

1. Platform Difficulty ❌ EASY (Opus 100% / GPT 80%) after fold docs +
   verifier rebuild. Sufficiency PASS; near-miss was preflight idempotency.
2. Primary activity collapsed to patching three C/Go polarity stubs.
3. Human review: replacing `/opt/ingest/bin` with bash stand-ins passed
   until verifier rebuild; rebuild blocked stand-ins but did not restore
   hardness (still debugging).

## Redesign

- Keep `system-administration` + lease/mount cutover objective.
- Prebuilt correct `ringfan` / `preflight` / `healthctl` (sources builder-only).
- Broken ops under `/app/ops/`; live state `/etc/ingest` + `/var/lib/ingest`.
- Graded entrypoint `/app/ops/run_cutover.sh` (tests re-invoke it).
- Coupled loci: fleet≠harbor lease, compound seal+mode, multi-drop-in fold,
  decoy skim, dual-residency seat, seal_gen arm, activation roster-only,
  preflight rematerialize + stable re-run.
- Instruction symptoms/outcomes only; no make/rebuild recipe.
