### Decision
GO — Attempt 1. SoftHSM-class OpenVPN CCD seating: durable prefer × tip bind × abort rematerialize × generation floors × overlapping pool decoy; bash ops under live `/etc/openvpn` + `/var/lib/openvpn/ops`; no source-repair framing.

### Metadata
- version: 2
- Task name: openvpn-ccd-route-push-seating
- Title: OpenVPN CCD Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["openvpn", "ccd", "iroute", "pool-prefer", "generation-gate", "ops-journal"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat client-config-dir routing so `/app/ops/run_ovpn_seat.sh` writes `/output/ovpn-seat.json` with `schema_tag` (string `ovpn-seat-v1`), `clients` (array of `{cn, iroute, generation, pushed}`), `pools` (array of `{name, cidr, active}`), and `seat_ok` (boolean). Live server config under `/etc/openvpn/server/` and CCD under `/etc/openvpn/ccd/`; durable prefer + CCD journal under `/var/lib/openvpn/ops/`. A client is pushed only when its iroute matches the durable journal tip at generation ≥ floor, the pool is prefer-selected (not the live overlapping decoy), and a later ccd.abort fragment does not revoke it. `/usr/local/bin/ovpnhealth` may print connected while `seat_ok` is false. Frozen fixtures under `/app/data/ovpn/` stay intact. Verifier re-invokes seating; two runs byte-identical; hand-authored JSON fails.

### Failure topology
Broken baseline ships live/surface preference, stale tip bind, abort residue always rematerialized into live server drop-ins, CCD apply that pushes every roster CN, and end-of-pipeline surface rematerialize that undoes naive CCD edits. Overlapping decoy pool can green client rows while `seat_ok` stays false. Correct seating couples prefer mode, tip bind matching `gen.target`, sealed complete prefer batch tip iroutes, client journal admit−revoke, durable floors, folded abort set, site-standard live drop-in, and cutover receipt.

### Environment shape
- `/app/ops/` seating entrypoint + opaque abort/tip helpers
- `/app/rim/`, `/app/bag/`, `/app/wire/`, `/app/deck/` opaque fold/journal/apply/rematerialize/emit
- `/app/docs/` layout + seating contract outcomes
- `/app/config/` site-standard tokens + surface prefer seed
- `/app/data/ovpn/` frozen client fixtures + seed materials
- Live `/etc/openvpn/{server,ccd}/` and durable `/var/lib/openvpn/`
- Surface health `/usr/local/bin/ovpnhealth`

### Required artifacts
Standard task layout: instruction.md, task.toml, output_contract.toml, environment/Dockerfile + .dockerignore + hashed requirements, ops/docs/config/data/helpers, solution/solve.sh, tests/test.sh + test_outputs.py. ≥20 environment files excluding Dockerfile.

### Test plan
- Schema + seat_ok + mixed pushed polarity (flint/beryl/mica true; quartz/jasper/onyx false)
- Byte-identical dual seat + gen.live == gen.target
- Tip iroute state records match prefer journal + report
- Sealed complete tip beats incomplete later batch
- Revoked journal CN never pushed
- Abort forensic vs live site-standard
- Stale cutover receipt rematerializes abort then site-standard wins; live drop-in remains
- Abort set excludes onyx; flint/beryl still pushed
- Pool matrix: only prefer-selected pool active; overlapping decoy inactive
- Full client matrix tip × journal × floor × abort
- Quartz below durable floor
- Live CCD files carry durable iroutes (not surface bait)
- ovpnhealth connected ≠ sufficient
- Clear pushed.set + reseat reconstitutes
- Prefer flip to live poisons via rematerialize; durable recovers

### Drafting guardrails
Symptoms instruction; outcomes in docs; no helper names; no iroute matrix in site_standard; ship correct fold/journal/emit; residual broken = abort gate + tip resolve/bind/cutover + CCD apply + prefer×bind rematerialize; mineral test names; opaque fix symbols.

### Triviality Ledger
- Grepping four polarity helpers without prefer×bind rematerialize fails dual-seat and y3-class prefer re-entry.
- Hand-writing `/output/ovpn-seat.json` fails verifier re-entry.
- Selecting overlapping live decoy pool greens some clients but fails seat_ok + pool.active asserts.
- Deleting live `90-local.conf` to “suppress abort” fails flint-class presence + fold coupling.
- Incomplete later prefer batch tip weights/iroutes fail coral-class tip asserts.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites helpers with substantive logic, not delete-only.
- RC2: no broken_/fix_me_/golden_ names.
- RC3: tests assert domain matrix + live CCD + pools, not schema alone.
- RC4/RC5: EXPECTED recomputed from durable fixtures in tests.
- RC6: instruction symptoms + doc outcomes, not fix recipes.
- RC7: solve.sh substantive (≥80 LOC comfortable).
- GX9/GX10: no answer-key triples; no polarity contradictions.
- Static: allow_internet=false; hashed pytest; PLW1510 check=; no COPY hidden paths.

### Initial Draft Commitments
- tasks/openvpn-ccd-route-push-seating/instruction.md
- tasks/openvpn-ccd-route-push-seating/task.toml
- tasks/openvpn-ccd-route-push-seating/output_contract.toml
- tasks/openvpn-ccd-route-push-seating/solution/solve.sh
- tasks/openvpn-ccd-route-push-seating/tests/test.sh
- tasks/openvpn-ccd-route-push-seating/tests/test_outputs.py
- tasks/openvpn-ccd-route-push-seating/environment/Dockerfile
- tasks/openvpn-ccd-route-push-seating/environment/.dockerignore
- tasks/openvpn-ccd-route-push-seating/environment/requirements.txt
- tasks/openvpn-ccd-route-push-seating/environment/ops/run_ovpn_seat.sh
- tasks/openvpn-ccd-route-push-seating/environment/ops/helm_r.sh
- tasks/openvpn-ccd-route-push-seating/environment/ops/axle_n.sh
- tasks/openvpn-ccd-route-push-seating/environment/rim/mesh_k.sh
- tasks/openvpn-ccd-route-push-seating/environment/rim/scan_t.sh
- tasks/openvpn-ccd-route-push-seating/environment/bag/skim_p.sh
- tasks/openvpn-ccd-route-push-seating/environment/bag/note_u.sh
- tasks/openvpn-ccd-route-push-seating/environment/wire/sock_v.sh
- tasks/openvpn-ccd-route-push-seating/environment/wire/knit_q.sh
- tasks/openvpn-ccd-route-push-seating/environment/deck/emit_m.sh
- tasks/openvpn-ccd-route-push-seating/environment/tools/ovpnhealth
- tasks/openvpn-ccd-route-push-seating/environment/docs/layout.md
- tasks/openvpn-ccd-route-push-seating/environment/docs/seating_contract.md
- tasks/openvpn-ccd-route-push-seating/environment/docs/operator-notes.md
- tasks/openvpn-ccd-route-push-seating/environment/config/site_standard.conf
- tasks/openvpn-ccd-route-push-seating/environment/config/prefer.surface.toml
- tasks/openvpn-ccd-route-push-seating/environment/packaging/README.md
- tasks/openvpn-ccd-route-push-seating/environment/data/build_fixtures.sh
- tasks/openvpn-ccd-route-push-seating/environment/data/roster.list
- tasks/openvpn-ccd-route-push-seating/environment/data/ovpn/*.toml (6 clients)
- tasks/openvpn-ccd-route-push-seating/environment/data/seed/** (server.conf, conf.d, abort.d, ccd, surface, journals, floors, pools, tip_bind)

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: ops/helm_r.sh
  symbol: helm_r
  kind: function
  signature: helm_r()
  purpose: receipt-gated copy of abort package into live server drop-in
- path: ops/axle_n.sh
  symbol: axle_n
  kind: function
  signature: axle_n()
  purpose: resolve sealed complete prefer tip rows, write tip records, bind, site-standard, cutover
- path: wire/sock_v.sh
  symbol: sock_v
  kind: function
  signature: sock_v()
  purpose: apply tip iroutes to live CCD and compute pushed set
- path: wire/knit_q.sh
  symbol: knit_q
  kind: function
  signature: knit_q()
  purpose: prefer×bind-gated rematerialize of surface CCD and tip seeds
```

#### flipping_point_contract
```
locations:
  - id: A
    path: ops/helm_r.sh
    controls_tests: [test_h8_amber, test_c1_flint]
  - id: B
    path: ops/axle_n.sh
    controls_tests: [test_w7_quartz, test_v5_coral, test_c1_flint, test_y3_jasper]
  - id: C
    path: wire/sock_v.sh
    controls_tests: [test_q3_topaz, test_p9_jade, test_r6_slate, test_u2_mica, test_m1_opal]
  - id: D
    path: wire/knit_q.sh
    controls_tests: [test_k5_garnet, test_y3_jasper, test_n4_beryl]
concentration_cap: 0.45
```

#### code_forbidden_tokens
[openvpn, ccd, iroute, pool, prefer, generation, seat, abort, journal, tip, clients, pushed, rematerialize, durable, surface, route, push]
