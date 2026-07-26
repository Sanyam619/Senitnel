The mesh under /app/ is mid-cutover between Workload API SVID issuance on the Go side and Java services that authenticate peers through KeyStore and TrustManager material plus a custom SPI.

Observed behavior:
- `/app/bin/readycheck` prints readiness OK.
- Fresh RPCs and resumed RPCs disagree on the same peer material.
- Chains with an intermediate outside the valid time window pass under a warm TrustManager cache pinned to that chain's root.
- SPI subject checks that match the legacy global subject disagree with the root-scoped binding table for the post-flip root.
- The live bundle names the pre-flip root and generation; runtime names the post-flip target.
- Some cutover driver entries still only mirror side material, view the cache, or list scenarios.

Bring live-bundle publish, TrustManager cache rebind, and session-ticket floor into agreement with `/app/ops/mesh-notes.toml`. `/app/bin/meshctl probe` must write `/output/mesh-cutover.json` matching those notes for every scenario under `/app/data/scenarios/`. The report must come from a real meshctl probe run, not a hand-written stand-in. Do not alter fixtures under `/app/data/fixtures/`.

The probe report uses schema_version mesh-cutover-1 at the top level, with integer epoch matching `/app/data/state/runtime.json`, and a cases array. Each case has string id, string decision (accept or reject), string reason_code, string handshake (fresh or resumed), and integer trust_epoch. Required per-scenario values live in `/app/ops/mesh-notes.toml`.
