# SoftHSM trust notes

Working tree is `/app`. Deep admission is the trust authority for recovery;
the surface path is triage-only and must not be treated as host admit decisions.

## Commands

- `/app/ops/run-desk.sh <path>` — publish deep trust ledger (and quarantine sidecar)
- `/app/bin/trusteval attest --out <path>` — deep trust attestation
- `/app/bin/surfcheck --out <path>` — surface triage check (not trust authority)
- `/app/bin/framecheck --frame <path>` — deep integrity probe for one credential frame

## Layout

| Path | Contents |
|------|----------|
| `/app/ops/` | Policy, preference, matrix, runbooks, admission entrypoint |
| `/app/config/profiles/` | Fleet profile epoch assignments |
| `/app/data/signed_segments/` | Signed WAL segments |
| `/app/data/credentials/` | Authenticated credential feeds |
| `/app/data/manifests/` | Signing-authority manifests |
| `/app/data/ledger/` | Revocation ledger |
| `/app/data/fixtures/` | Audit anchors and surface snapshots |
| `/app/data/fixtures/surface_attestation.json` | Last known surface attestation snapshot |
| `/app/data/fixtures/seed.json` | Fixture preservation marker |
| `/app/data/fixtures/dynamic_test_frame.bin` | Lab probe frame (authentic) |
| `/app/data/fixtures/dynamic_test_injected.bin` | Lab probe frame (wrong signer) |
| `/app/data/fixtures/dynamic_test_legacy.bin` | Lab probe frame (legacy payload-only) |

Do not rewrite `/app/data/fixtures/` during routine admission runs. Lab drills may drop temporary segments such as `seg_98.bin` / `seg_99.bin` under `/app/data/signed_segments/`.

`/app/bin/surfcheck` is the quick surface check used during triage. Deep admission for recovery uses the desk entrypoint above.

Scratch attestation writes during lab verification may land under `/tmp` as `sign-ledger-verify.json`, `sign-ledger-dynamic.json`, `sign-ledger-second.json`, or `sign-ledger-prefer.json`.
