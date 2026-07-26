# Hydrologic gauge model notes

The pre-built rollup index under `/app/store` maintains stage-sum and count
totals for gauge series used in rating-curve and basin water-balance checks.
The basin-window helper under `/app/lane` evaluates the same epoch window for
cross-check purposes. Operator tables under `/app/config/l7/` select knobs
those tools read. Site trust policy under `/app/ops/` constrains which journal
lineage states may be restored and whether a live revocation ledger is required.

When the active generation, barrier cutoff, revocation ledger, and sidecar
attestation disagree, stage-sum totals and basin-window probes diverge even
though individual reading archives still look intact. Telemetry series outside
an incident remain on their own sidecar generation — do not rebuild that
channel during primary-gauge recovery.
