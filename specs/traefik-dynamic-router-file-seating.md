### Decision
GO — Attempt 1. SoftHSM-class Traefik file-provider seating lattice: durable prefer × tip_bind × journal tip (retired decoys) × middleware prefer sheet × abort rematerialize/cutover receipt × generation floors. Opaque bash helpers; symptoms-only instruction; no repair/debug framing.

### Metadata
- version: 2
- Task name: traefik-dynamic-router-file-seating
- Title: Traefik Router Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["traefik", "dynamic-router", "middleware", "file-provider", "generation-gate", "ops-seating"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat reverse-proxy routes so `/app/ops/run_traefik_seat.sh` writes `/output/traefik-seat.json` with schema_tag=`traefik-seat-v1`, routers[{name,rule,service,generation,active}], middlewares[{name,type,attached}], seat_ok. Live file provider under `/etc/traefik/` + `/etc/traefik/dynamic/`; durable prefer + route journal under `/var/lib/traefik/ops/`. Active only when rule/service match durable journal tip at generation ≥ floor. Middleware attachments follow durable prefer. Abort rematerialize unless cutover.ok key=value gen+mode=seal; abort must not revoke seated routers; live drop-in remains with site-standard. traefikhealth may print routed while seat_ok false. Frozen `/app/data/traefik/` intact. Verifier clears /output and re-invokes; two runs byte-identical.

### Failure topology
Broken seating rematerializes surface seeds and abort residue, reads live middleware decoys, and stamps seat_ok true from surface health. Greening one router without prefer+bind rematerializes; greening middleware without tip/floor fails router cells.

### Environment shape
Live Traefik tree, durable ops (prefer/tip_bind/journal/retired/floors/abort/mw_prefer/seeds/state), opaque helpers under ops/rim/bag/wire/deck, frozen fixtures, surface health CLI, outcome docs.

### Required artifacts
Standard task layout with ≥20 environment files excluding Dockerfile.

### Test plan
Fourteen mineral-named tests covering schema, idempotency, fixture pin, tip rule/service, floor active polarity, middleware prefer, abort forensic, cutover receipt, abort-not-revoke, EXPECTED equality, roster matrix, health bait, prefer re-entry rematerialize, novel tip inject.

### Drafting guardrails
No repair/debug verbs; opaque fix-path symbols; seeds never contain answers; EXPECTED in tests.

### Triviality Ledger
- Patching only dynamic YAML fails under knit_q rematerialize until prefer+bind gate.
- All-active=true fails floor-coupled cells.
- Live middleware chain fails prefer sheet cells.
- Deleting abort drop-in fails receipt+presence cells.
- Hand-written JSON fails verifier re-entry.

### Per-gate Pitfall Inventory
- RC1: Oracle rewrites helper bodies + prefer/bind, not delete markers.
- RC2: No broken_/golden_ names; mineral tests.
- RC3: Tests recompute EXPECTED from fixtures.
- RC4/RC5: No answer JSON under environment/.
- RC6: Symptoms-only instruction.
- RC7: Oracle substantive LOC across helpers.
- GX9/GX10: No answer recital / polarity contradiction.
- Static: allow_internet=false; hashed requirements; PLW1510 check=; .dockerignore.

### Initial Draft Commitments
- tasks/traefik-dynamic-router-file-seating/instruction.md
- tasks/traefik-dynamic-router-file-seating/task.toml
- tasks/traefik-dynamic-router-file-seating/output_contract.toml
- tasks/traefik-dynamic-router-file-seating/environment/Dockerfile
- tasks/traefik-dynamic-router-file-seating/environment/.dockerignore
- tasks/traefik-dynamic-router-file-seating/environment/requirements.txt
- tasks/traefik-dynamic-router-file-seating/environment/docs/layout.md
- tasks/traefik-dynamic-router-file-seating/environment/docs/seating_contract.md
- tasks/traefik-dynamic-router-file-seating/environment/docs/operator-notes.md
- tasks/traefik-dynamic-router-file-seating/environment/config/site_standard.yml
- tasks/traefik-dynamic-router-file-seating/environment/ops/run_traefik_seat.sh
- tasks/traefik-dynamic-router-file-seating/environment/ops/helm_r.sh
- tasks/traefik-dynamic-router-file-seating/environment/ops/axle_n.sh
- tasks/traefik-dynamic-router-file-seating/environment/ops/run.list
- tasks/traefik-dynamic-router-file-seating/environment/wire/knit_q.sh
- tasks/traefik-dynamic-router-file-seating/environment/rim/mesh_k.sh
- tasks/traefik-dynamic-router-file-seating/environment/rim/scan_t.sh
- tasks/traefik-dynamic-router-file-seating/environment/bag/skim_p.sh
- tasks/traefik-dynamic-router-file-seating/environment/bag/note_u.sh
- tasks/traefik-dynamic-router-file-seating/environment/deck/emit_m.sh
- tasks/traefik-dynamic-router-file-seating/environment/tools/traefikhealth
- tasks/traefik-dynamic-router-file-seating/environment/data/roster.list
- tasks/traefik-dynamic-router-file-seating/environment/data/build_fixtures.sh
- tasks/traefik-dynamic-router-file-seating/environment/data/traefik/alpha.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/traefik/beta.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/traefik/gamma.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/traefik/delta.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/traefik/epsilon.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/traefik.yml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/journal.jsonl
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/retired_tips.jsonl
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/prefer.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/tip_bind.accept
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/mw_prefer.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/floors.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/live_floors.toml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/abort.d/90-abort.yml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/dynamic/10-routers.yml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/dynamic/40-middlewares.yml
- tasks/traefik-dynamic-router-file-seating/environment/data/seed/seeds/10-routers.yml
- tasks/traefik-dynamic-router-file-seating/environment/packaging/traefik.sha256
- tasks/traefik-dynamic-router-file-seating/environment/packaging/README.md
- tasks/traefik-dynamic-router-file-seating/solution/solve.sh
- tasks/traefik-dynamic-router-file-seating/tests/test.sh
- tasks/traefik-dynamic-router-file-seating/tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: ops/helm_r.sh
  symbol: helm_r
  kind: function
  signature: helm_r()
  purpose: abort drop-in vs cutover receipt
- path: ops/axle_n.sh
  symbol: axle_n
  kind: function
  signature: axle_n()
  purpose: journal tip materialize
- path: wire/knit_q.sh
  symbol: knit_q
  kind: function
  signature: knit_q()
  purpose: surface seed rematerialize gate
- path: rim/mesh_k.sh
  symbol: mesh_k
  kind: function
  signature: mesh_k()
  purpose: dynamic fold without abort revoke
- path: bag/skim_p.sh
  symbol: skim_p
  kind: function
  signature: skim_p()
  purpose: middleware prefer sheet apply
- path: deck/emit_m.sh
  symbol: emit_m
  kind: function
  signature: emit_m()
  purpose: write seating ledger JSON

#### flipping_point_contract
```
{
  "locations": [
    {
      "id": "A",
      "path": "ops/helm_r.sh",
      "controls_tests": [
        "test_h8_amber",
        "test_c1_flint",
        "test_r6_slate",
        "test_u2_mica",
        "test_q3_topaz"
      ]
    },
    {
      "id": "B",
      "path": "wire/knit_q.sh",
      "controls_tests": [
        "test_j2_onyx",
        "test_v5_coral",
        "test_u2_mica",
        "test_m1_opal",
        "test_n4_beryl"
      ]
    },
    {
      "id": "C",
      "path": "bag/skim_p.sh",
      "controls_tests": [
        "test_p9_jade",
        "test_u2_mica",
        "test_s8_garnet",
        "test_m1_opal",
        "test_t4_pearl"
      ]
    },
    {
      "id": "D",
      "path": "ops/axle_n.sh",
      "controls_tests": [
        "test_v5_coral",
        "test_d6_obsidian",
        "test_m1_opal",
        "test_w7_quartz"
      ]
    }
  ],
  "no_single_location_flips_majority": true,
  "concentration_cap": 0.5
}
```

#### decoy_manifest
- path: rim/scan_t.sh
  kind: helper
  rhymes_with: mesh_k
  non_fix_purpose: lists dynamic filenames for operator notes
- path: bag/note_u.sh
  kind: helper
  rhymes_with: skim_p
  non_fix_purpose: writes /var/log/traefik/seat.note
- path: tools/traefikhealth
  kind: helper
  rhymes_with: emit_m
  non_fix_purpose: surface routed bait

#### code_forbidden_tokens
```
code_forbidden_tokens: ["traefik", "router", "routers", "rule", "service", "generation", "middleware", "middlewares", "seat", "seating", "schema", "schema_tag", "active", "attached", "seat_ok", "prefer", "journal", "floor", "abort", "dynamic", "provider", "file", "output", "fixture", "health", "receipt", "durable", "live", "tip", "fragment", "ledger", "ops"]
```
