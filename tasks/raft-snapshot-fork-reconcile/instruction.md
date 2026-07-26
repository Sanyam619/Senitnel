After a control-plane crash, point lookups and range scans on the events namespace under `/app/data` disagree with what the on-disk journal chain says should be visible. Metrics was not part of the fork.

Recovery is operational: edit operator tables under `/app/config/l7/`, Go sources under `/app/lane/`, and rebuild `/app/bin/lane`. Run `/app/bin/ctl` for recovery operations. See `/app/ops/runbooks/ctl_usage.md` for subcommands and operator table fields. Do not patch the prebuilt Rust ctl sources.

When events queries line up again, emit `/output/fork-report.json` (via `ctl report` or `lane emit`). Include integer `restored_generation` (positive, not above `ceiling_gen` from `ctl status`), and `events` / `metrics` objects each with integer `visible_segments` and hex `sidecar_digest` matching the on-disk sidecar for that namespace under `/app/data/sidecars/`. Range scans at your probe timestamp should list the same keys in sorted order with matching payloads as `/app/bin/ctl query`.
