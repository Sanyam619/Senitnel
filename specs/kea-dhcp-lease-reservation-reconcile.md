### Decision
GO — Attempt 1. Sysadmin Kea DHCP4 seating desk: live `/etc/kea` + `/var/lib/kea` authority coupling (prefer × conf.d fold × memfile × generation × cutover), bash-only, no source-repair framing.

### Metadata
- version: 2
- Task name: kea-dhcp-lease-reservation-reconcile
- Title: Kea DHCP Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [kea, dhcp, reservation, lease-memfile, conf-fold, generation-gate]
- Milestones: 0

## Authoring Brief

### Public contract
Seat Kea DHCP4 via `/app/ops/run_dhcp_seat.sh` into `/output/dhcp-seat.json` with schema_tag, subnets, reservations, conflicts, seat_ok. Live state under `/etc/kea/` and `/etc/kea/kea-dhcp4.d/`; durable prefer + memfile under `/var/lib/kea/ops/`. Frozen `/app/data/kea/` pinned. keahealth may OK while seat_ok false. Entrypoint twice → byte-identical; verifier re-seats after wiping `/output`.

### Failure topology
Broken abort rematerialize, live-floor tip pick, first-file fold, ignored memfile, live decoy pools, and always-green emit interact. Honoring one reservation can force a distant duplicate/shadow conflict. Surface health is non-authoritative.

### Environment shape
ops/rim/bag/deck/wire helpers, tools/keahealth, docs seating contract, config site_standard, data/kea fixtures + seed, packaging pin.

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/*, solution/solve.sh, tests/{test.sh,test_outputs.py}

### Test plan
14 mineral tests: schema/seat_ok, idempotence, pin, site fold, journal/floor, lease collision, abort forensic, cutover receipt, durable prefer pools, full EXPECTED, honor matrix, duplicate conflict, shadow conflict, health bait.

### Drafting guardrails
No repair/debug framing; symptoms seating language; opaque helper names; EXPECTED from durable fixtures; no answer-key counts in instruction.

### Triviality Ledger
- Always-green emit alone fails re-entry + live-state tests (j2/v5/r6/c1).
- First-file fold greens one drop-in but fails shadow/duplicate matrix.
- Live decoy pools fail durable pool equality and honor matrix.
- Ignoring memfile honors colliding IP and fails jade.
- Deleting live 90-local on cutover fails flint (suppress ≠ delete).

### Per-gate Pitfall Inventory
- RC1: oracle rewrites helper bodies with substantive logic, not flag deletes.
- RC2: mineral test names; opaque helpers.
- RC3: domain honor/conflict asserts, not schema-only.
- RC4/RC5: EXPECTED recomputed in tests; packaging pin.
- RC6: symptoms instruction; contract details in docs.
- RC7: solve.sh >> 80 LOC.
- GX9/GX10: no per-row answer recital or polarity contradiction in instruction.

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml, construction_manifest.json
- environment/Dockerfile, .dockerignore, requirements.txt
- environment/ops/{run_dhcp_seat,helm_r,axle_n}.sh
- environment/rim/{mesh_k,scan_t}.sh
- environment/bag/{skim_p,note_u}.sh
- environment/deck/emit_m.sh
- environment/wire/{bind_v,knit_q}.sh
- environment/tools/keahealth
- environment/docs/{layout,seating_contract,operator-notes}.md
- environment/config/site_standard.conf
- environment/data/{roster.list,build_fixtures.sh,kea/*.toml,seed/**}
- environment/packaging/{README.md,kea.sha256}
- solution/solve.sh, tests/{test.sh,test_outputs.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
See construction_manifest.json (helm_r, axle_n, mesh_k, skim_p, bind_v, emit_m).

#### flipping_point_contract
See construction_manifest.json (≥3 locations, concentration_cap 0.5).

#### decoy_manifest
note_u, knit_q, scan_t.

#### code_forbidden_tokens
schema_tag, subnets, reservations, conflicts, seat_ok, honored, keahealth, memfile, cutover, generation, reservation, lease, shadowed, duplicate
