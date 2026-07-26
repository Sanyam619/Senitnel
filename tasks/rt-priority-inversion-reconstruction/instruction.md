Periodic release windows are slipping on several traced workloads under `/opt/kernlab/`. The probe at `/opt/kernlab/bin/kernprobe` walks `/opt/kernlab/config/manifest.txt` and writes `/output/analysis.json`, but replay proof with `/opt/kernlab/bin/klreplay` still fails and the analysis rows do not line up with the captures.

Rebuild what is needed under `/opt/kernlab/`, rerun the probe, and get a clean replay pass on every manifest row. Output field names and replay stdout expectations are documented under `/opt/kernlab/docs/`.

Deliver `/output/analysis.json` at version `1` with one entry per manifest id under `scenarios`. Each row includes `missed_deadline_task`, `chain`, and `ceilings` as defined in `/opt/kernlab/docs/analysis_schema.txt`.
