# Companion mesh attestation notes

Working tree is `/app`. Deep attestation is mesh admit authority for recovery;
the surface path is triage-only.

## Commands

- `/app/bin/trusteval attest --out <path>` — deep mesh attestation
- `/app/ops/run_mesh_attest.sh <path>` — deep-path attestation entrypoint
- `/app/bin/surfskim --out <path>` — surface triage check (not mesh admit authority)

## Layout

| Path | Contents |
|------|----------|
| `/app/ops/` | Policy, matrix, runbooks, attestation entrypoint |
| `/app/ops/prefer.toml` | Authority-source preference (surface baseline vs durable) |
| `/app/ops/tip_bind.accept` | Durable-authority bind acceptance receipt |
| `/app/config/profiles/` | Fleet profile epoch assignments |
| `/app/data/signed_segments/` | Signed WAL segments |
| `/app/data/credentials/` | Authenticated credential feeds |
| `/app/data/manifests/` | Signing-authority manifests, one file per tier (seed material per epoch) |
| `/app/core/src/lib.rs` | Shared lattice helpers used by deep attestation |
| `/app/data/ledger/` | Revocation ledger |
| `/app/data/fixtures/` | Audit anchors, surface snapshots, dynamic capture samples |

Do not rewrite `/app/data/fixtures/` during routine attestation runs. Live capture refresh may drop additional segments under `/app/data/signed_segments/`.

`/app/bin/surfskim` is triage-only. Deep attestation for recovery uses `trusteval` via `run_mesh_attest.sh`. Attestation JSON and the sibling reject ledger are written to the `--out` path passed to `attest` (default publish path `/output/mesh-attestation.json`).

Empty authority seeds and all-zero derived authority material must fail closed on the deep path: frames are not auto-accepted, and seal_break appears in the reject ledger.

A build-time authority guard reverts evaluator source repairs to the surface baseline on every rebuild until the durable-authority preference is committed under `/app/ops/` (durable source plus a bind acceptance naming the policy-selected authority class). Until then the rebuilt evaluator keeps emitting surface-shaped output regardless of source edits.

## Fixtures

`/app/data/fixtures/` holds the last surface snapshot, a pre-incident audit log, and dynamic capture samples.
