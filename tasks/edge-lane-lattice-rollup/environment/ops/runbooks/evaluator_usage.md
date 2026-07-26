# Fleet trust attestation notes

Working tree is `/app`. Deep attestation is the trust authority for recovery;
the surface path is triage-only. Durable preference must beat live surface bind
so material and admit-path bodies survive rebuild.

## Commands

- `/app/bin/trusteval attest --out <path>` — deep trust attestation
- `/app/ops/run_attestation.sh <path>` — rebuild deep path, then attest
- `/app/bin/surfpoke --out <path>` — surface triage check (not trust authority)

## Layout

| Path | Contents |
|------|----------|
| `/app/ops/` | Policy, matrix, preference, runbooks, attestation entrypoint |
| `/app/config/profiles/` | Fleet profile epoch assignments |
| `/app/data/signed_segments/` | Signed WAL segments |
| `/app/data/credentials/` | Authenticated credential feeds |
| `/app/data/manifests/` | Signing-authority manifests |
| `/app/data/ledger/` | Revocation ledger |
| `/app/data/fixtures/` | Audit anchors and surface snapshots |
| `/app/data/fixtures/surface_attestation.json` | Last known surface attestation snapshot |
| `/app/data/fixtures/seed.json` | Fixture preservation marker |
| `/app/data/fixtures/dynamic_test_frame.bin` | Lab probe frame (authentic) |
| `/app/data/fixtures/dynamic_test_injected.bin` | Lab probe frame (injected) |

## Epoch scenarios

- Epoch 25 does not publish: required lane is only revoked.
- Epoch 30 publishes under hold co-presence; accepted stays reduced versus a
  no-hold reading of the same stream.
- Watermark fences include the boundary timestamp.
- Deep accepted tallies stay strictly below the surface fixture on shared epoch ids.

Do not rewrite `/app/data/fixtures/` during routine attestation runs. Lab drills may drop temporary segments such as `seg_98.bin` / `seg_99.bin` under `/app/data/signed_segments/`.

`/app/bin/surfpoke` is the quick surface check used during triage. Deep attestation for recovery uses `trusteval` via `run_attestation.sh`.

Scratch attestation writes during lab verification may land under `/tmp` as `trust-attestation-verify.json`, `trust-attestation-dynamic.json`, or `trust-attestation-second.json`.
