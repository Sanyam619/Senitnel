Companion mesh admit under `/app` is split from triage. `/app/bin/surfskim` and `/app/data/fixtures/surface_attestation.json` look healthy. That path is not mesh admit authority. Forged, replayed, and revoked credentials inflate the surface path. Sibling epochs disagree on usable material. Dynamic fixtures under `/app/data/fixtures/` include an authentic frame and an injected frame the surface path ignores. Live capture may add further frames under `/app/data/signed_segments/`; authentic additions raise the deep tally for their epoch, and forged additions are refused.

Lane credential feeds under `/app/data/credentials/` and signed WAL segments under `/app/data/signed_segments/` are deep-path inputs. Fleet profiles under `/app/config/profiles/` and the matrix under `/app/ops/matrix.toml` assign epochs to profiles and decide which lanes must be present together. Policy and signing manifests under `/app/ops/` and `/app/data/manifests/` select the authority tier for keyed integrity. Forensic captures under `/app/data/fixtures/` include a pre-incident audit log. Do not treat the surface roster as deep authority.

Publish `/output/mesh-attestation.json` via `/app/ops/run_mesh_attest.sh` (rebuilds then runs `trusteval attest --out <path>`; default out path `/output/mesh-attestation.json`). Schema version is 1 with backends (name, status active or inactive) and epochs (id, profile, accepted). Also publish `/output/reject-ledger.json` alongside that attestation (version 1) with a rejected array of rows carrying epoch, lane, ts, and reason.

Reject reasons:
- seal_break — WAL frame that fails keyed integrity under deep authority
- replay — among integrity-valid signed WAL frames, timestamps must strictly advance within each epoch-and-lane stream. That stream is continuous across segment files: capture order is segment filename order, then frame order inside each segment, and the last accepted WAL timestamp for an epoch-and-lane carries into later segments. The first integrity-valid frame of a later segment is a replay when its timestamp does not strictly advance past that carried watermark. Equal timestamps likewise fail to advance. Example: if an earlier segment leaves one epoch-and-lane stream’s last accepted WAL timestamp at 100, then a later segment’s first integrity-valid frame on that same stream at 90 (or again at 100) is a replay; a later integrity-valid frame at 110 on that stream is not. A replay does not move the carried watermark — only a newly accepted WAL frame does. Credential-feed rows contribute to attestation tallies but do not establish or advance the WAL replay watermark.
- revoked — WAL frame rejected by the revocation ledger under `/app/data/ledger/`

Authority material fails closed: empty seed rows in the selected signing-authority manifests, or derived authority material that is all zeros, must not auto-accept WAL frames — accepted falls and seal_break appears in the reject ledger.

A build-time authority guard protects the deep path. While the authority-source preference under `/app/ops/` still points at the surface baseline, every rebuild rematerializes the evaluator sources from that baseline, so source-level repairs alone do not survive a rebuild and the deep path keeps producing surface-shaped output. Committing the durable-authority preference — selecting the durable source and binding acceptance to the authority class the trust policy selects — is what lets the guard stand down so a corrected evaluator can take effect.

How deep `accepted` is derived (exact integers come from a correct rebuild of trusteval, not from the surface fixture or hand-written JSON):
- Both lane credential-feed rows and integrity-valid, non-replay WAL frames that survive revocation and the epoch admission watermark can raise the tally. Only Active frames on the profile’s matrix lanes count; Held/suspended and Revoked frames do not.
- Credential-feed rows are not seal-checked and are not part of the WAL replay stream, but they still follow the revocation/hold ledger and the same epoch admission watermark as WAL frames.
- Matrix `required-together` epochs publish only when every required lane shows Active or Held presence. Matrix `solo` epochs publish when any classified frames exist on that profile’s lanes; the tally still counts only Active frames on those lanes.
- Held/suspended co-presence keeps a required-together epoch published but never raises `accepted`.

Observed deep-path outcomes:
- Deep accepted tallies are strictly below the surface fixture for every shared epoch id.
- Epoch 25 does not publish (a required lane is only revoked). Epoch 30 does publish under fleet_a with a suspended required lane — suspension satisfies mutual-presence but does not raise accepted.
- Every epoch a fleet profile claims publishes, except the one held back above; each published epoch reports the profile that claims it. Backend status reflects whether the matrix keeps that lane in service.
- An authentic frame added under signed_segments is incorporated into the deep tally for its epoch; a forged frame is refused and must not raise accepted.

Deep attestation must disagree with the surface fixture, stay stable across identical re-attestation, and match a rebuild from `/app` sources. Hand-written stand-ins fail. Leave `/app/data/fixtures/` untouched.
