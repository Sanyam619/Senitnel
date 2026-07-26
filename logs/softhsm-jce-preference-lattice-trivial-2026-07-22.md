# softhsm-jce-preference-lattice — platform TRIVIAL (2026-07-22)

Artifact: `difficulty_check_artifact (7).zip`

## Scores
- Opus 100% (5/5), GPT-5.5 100% (5/5), oracle 100%, NOP 0%
- All 10 tests 10/10

## Collapse (from GPT trajectories ~ep4–8)
1. Instruction published freshness band **4–9** (NestK answer key).
2. GateSeal SHA-256 over five small ints was brute-forced to `(167,49,12,4,9)`.
3. Token hex dump revealed pack/mode; JNI hdr swap was a one-line fix.
4. AssembleY live-as-durable and desk-reload NestK rematerialize were readable.
5. Primary activity was debugging/transcription of preference sheets — not residual SoftHSM trust reasoning.

## Redesign shipped
Replace preference-lattice GateSeal desk with SoftHSM-framed WAL trust admission
(edge-lane / signed-plugin Attempt-6 class): opaque lane×strand material, sealed
`framecheck`, hold/revoke/replay/presence, surface `surfcheck` ≠ deep `trusteval`,
outputs `/output/sign-ledger.json` + quarantine. Complexity moved off constant
transcription.
