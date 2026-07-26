# WAL segment frame layout

Segments under `/app/data/signed_segments/` contain concatenated frames:

| Offset | Size | Field |
|--------|------|-------|
| 0 | 1 | magic `0xA5` |
| 1 | 1 | lane id (see `/app/ops/trust_policy.toml` `[lanes]`) |
| 2 | 2 | epoch id, big-endian |
| 4 | 2 | payload length, big-endian |
| 6 | N | payload text (`ts=<u64>;hold=<0|1>;tag=<id>`) |
| 6+N | 1 | integrity byte |

Lane identifiers and verification policy knobs live under `/app/ops/`. Capture-order segments are processed in filesystem name order. Forensic quarantine output is written alongside the attestation publish path.
