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

Lane identifiers and verification policy knobs live under `/app/ops/`. Integrity-valid WAL frames are replay-checked in one continuous per-(epoch, lane) stream: segment filename order, then in-frame order. The last accepted WAL timestamp for that stream carries across segment boundaries, so the first integrity-valid frame of a later segment is a replay when its timestamp does not strictly advance past the watermark from earlier segments. Equal or regressing timestamps are replays and belong in the reject ledger. Example: last accepted WAL timestamp 100 in an earlier segment makes a later segment’s opening integrity-valid frame at 90 or 100 a replay on that stream; 110 advances and is accepted. Replay rows do not move the carried watermark. Credential-feed rows contribute to attestation tallies but do not seed or advance the WAL replay watermark. Forensic reject-ledger output is written alongside the attestation publish path.

## Forensic samples

`/app/data/fixtures/pre_incident_audit.log` records working integrity samples sample_a and sample_b from before the incident (seed, material, and check fields). The dump does not annotate a transform.

