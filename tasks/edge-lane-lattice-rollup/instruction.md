Restore deep fleet credential trust attestation so forged, replayed, and revoked WAL frames no longer inflate the published trust view.

Fleet credential trust under `/app` is split. `/app/bin/surfpoke` and `/app/data/fixtures/surface_attestation.json` look healthy. That path is not trust authority. Forged WAL credentials, wrong-signer signatures, legacy WAL bindings that omit epoch/lane identity in the signed message, replayed timestamps, and revoked credentials inflate the surface path. Sibling epochs disagree on usable material. Live surface preference still wins over durable authority, and rebuilds rematerialize identity signing stubs, payload-only verify, and the no-replay admit path until durable preference is restored. Dynamic fixtures under `/app/data/fixtures/` include an authentic frame, a wrong-signer frame, and a legacy-bound frame the surface path ignores. Verifier probes may stage temporary segment files such as `seg_97.bin` under `/app/data/signed_segments/` during checks.

Lane credential feeds under `/app/data/credentials/` (`mqtt.jsonl`, `lora.jsonl`, `uart.jsonl`) are deep-path inputs. They contribute to accepted tallies subject to watermark and ledger rules. Only individual frames that fail deep verification or policy are excluded — do not drop those feeds wholesale. A pre-incident capture under `/app/data/fixtures/` records working verifier samples (sample_a, sample_b, sample_c) with seed, key domain (`domain_ascii=ELL2`), derived secret, public key, signed message, and signature hex. Use those samples to recover authority-tier material and message binding. Do not treat the surface roster as deep authority.

Publish `/output/trust-attestation.json` via `/app/ops/run_attestation.sh` (version 1; backends and epochs) as the verified trust view, and `/output/quarantine.json` (version 1; rejected rows with epoch, lane, ts, reason among integrity_failure, replay, revoked). Preference and epoch outcome notes live under `/app/ops/runbooks/evaluator_usage.md`.

Classification rules for quarantine:
- `integrity_failure` — WAL frame whose signature does not verify under deep authority (garbled trailer, wrong signer, or legacy payload-only binding).
- `replay` — within each epoch-and-lane stream, credential JSONL frames and integrity-accepted WAL frames interleave by ascending timestamp; a credential whose timestamp does not strictly advance on that interleaved stream is a replay (not per file, and not JSONL-then-WAL or WAL-then-JSONL as separate passes). Equal timestamps do not advance — the later frame on that stream is a replay. The base capture includes such non-advancing credentials on published epochs; quarantine must carry `replay` rows for those epochs, or accepted tallies inflate.
- `revoked` — WAL frame rejected by the revocation ledger.

Observed deep-path outcomes:
- Deep accepted tallies on published epochs stay strictly below the surface fixture for shared epoch ids; rebuilt `trusteval` is the source of truth.
- Epoch 25 does not publish (required lane is only revoked). Epoch 30 does publish under fleet_a with a suspended required lane — suspension satisfies mutual-presence but does not raise accepted.
- Published deep epochs are 10, 20, 30, 40, 50 (fleet_a on 10, 20, and 30; fleet_b on 40 and 50). Matrix lanes mqtt, lora, uart report active; canbus and zigbee report inactive.
- Watermark fences include the boundary timestamp.
- Ledger holds apply to credentials with timestamps strictly greater than the hold threshold; the on-boundary credential is not held.

Deep attestation must disagree with the surface fixture, stay stable across identical re-attestation, and match a rebuild from `/app` sources. Hand-written stand-ins fail. Leave `/app/data/fixtures/` untouched. Do not edit verifier tests or reward files.
