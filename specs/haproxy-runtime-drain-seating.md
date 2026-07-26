### Decision
GO — Attempt 1. Hard system-administration HAProxy runtime-drain backend seating with coupled conf.d fold × runtime socket apply × drain leases × durable generation floors × abort rematerialize receipt. Primary activity is live `/etc/haproxy` + `/var` ops seating, not load-balancer implementation or repair/debug framing.

### Metadata
- version: 2
- Task name: haproxy-runtime-drain-seating
- Title: HAProxy Drain Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["haproxy", "backend-seating", "runtime-socket", "drain-window", "generation-gate", "conf-fold"]
- Milestones: 0

## Authoring Brief

### Public contract
Live reverse-proxy state under `/etc/haproxy/`, `/etc/haproxy/conf.d/`, `/var/lib/haproxy/`, and `/var/run/haproxy/` must agree with durable backend authority. Entrypoint `/app/ops/run_proxy_seat.sh` must produce `/output/proxy-seat.json` with:

- `schema_tag` (string) equal to `proxy-seat-v1`
- `backends` — array of `{name, server, weight, drained, generation}`
- `socket_applied` (boolean)
- `seat_ok` (boolean)

Surface `/usr/local/bin/proxyhealth` may print UP while deep seating is wrong. Frozen fixtures under `/app/data/backends/` stay integrity-pinned. A server is in service only when generation ≥ durable floor, it is not drained, and runtime socket apply matches folded conf.d weights. Drain leases mark `drained` without zeroing weight. Two seating runs must leave byte-identical `/output/proxy-seat.json`.

### Failure topology
Authorities couple: lexical conf.d fold (later abort override), durable generation floors (live decoy floors disagree), drain leases vs weight-zero polarity, runtime socket apply that can leave `socket_applied` false when files look right, abort.d rematerialize unless durable `cutover.ok` (`key=value`, `gen=<target>`, `mode=seal`) while live `90-local.cfg` stays present with site-standard tokens, and ledger emit that sets `seat_ok` only on full agreement. Greening proxyhealth or editing only `haproxy.cfg` still fails distant mineral tests.

### Environment shape
- Broken ops helpers under `/app/rim`, `/app/ops`, `/app/bag`, `/app/deck`, `/app/wire`
- Decoy helpers under extra rim/bag/wire scripts
- Live host state under `/etc/haproxy`, `/var/lib/haproxy`, `/var/run/haproxy`
- Immutable fixtures under `/app/data/backends` plus packaging digests
- Outcome docs under `/app/docs`
- Surface health bait `/usr/local/bin/proxyhealth`

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (≥20 files excl. Docker), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`, `environment/.dockerignore`, hashed `requirements.txt`.

### Test plan
- `test_q3_topaz` — ledger schema + schema_tag + seat_ok true
- `test_n4_beryl` — double-run byte-identical output
- `test_w7_quartz` — `/app/data/backends` packaging digest pin
- `test_j2_onyx` — lexical fold effective weights match site standard
- `test_v5_coral` — generation ≥ durable floor polarity across roster
- `test_p9_jade` — drain lease marks drained without zeroing weight
- `test_h8_amber` — abort override residue + abort.d forensic package
- `test_c1_flint` — matching cutover.ok receipt; live 90-local present
- `test_r6_slate` — socket_applied true and runtime map matches fold
- `test_u2_mica` — backends array contents + seat_ok coupling
- `test_m1_opal` — full roster weight/drain/generation matrix
- `test_t4_pearl` — proxyhealth may still print UP (surface≠deep)

Each test accepts any correct seating end-state; none require oracle-only paths.
Not chain-dependent: each can set up via full entrypoint re-entry.

### Drafting guardrails
Symptoms-only instruction; fair outcomes in `/app/docs` (receipt format, drain≠weight-zero). Opaque fix-path symbols from construction manifest. No intent comments. No golden JSON under environment. Verifier re-enters seating and derives EXPECTED from durable fixtures. No repair/debug framing in instruction or tags.

### Triviality Ledger
- Hand-writing `/output/proxy-seat.json` fails because verifier deletes output and re-enters `/app/ops/run_proxy_seat.sh` twice.
- Editing only `haproxy.cfg` fails because conf.d fold + abort rematerialize own effective weights.
- Zeroing drained-backend weight fails `test_p9_jade` (drain lease keeps weight, sets drained).
- Matching files without socket apply fails `test_r6_slate` (`socket_applied` false).
- Using live `/etc/haproxy/floors` fails distant generation cells against durable floors.
- Leaving `seat_ok` always true fails when any backend or socket disagrees.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites substantive helper bodies (not delete BUG markers).
- RC2: no broken_/golden_/expected_ names on solver-visible surfaces.
- RC3: tests assert computed weight/drain/generation/socket values, not schema alone.
- RC4/RC5: EXPECTED in tests; no golden under environment/.
- RC6: instruction symptoms-only; outcomes not fix recipes.
- RC7: oracle LOC ≥30 substantive lines.
- GX9/GX10: no per-backend answer-key recital; no polarity contradiction in one sentence.
- Static: `allow_internet=false`; hashed requirements; PLW1510 `check=`; `.dockerignore`.
- Category: grade live `/etc`/`/var` via bash ops; languages=`["bash"]`; no repair/debug framing.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/ops/run_proxy_seat.sh
- environment/ops/axle_n.sh
- environment/ops/helm_r.sh
- environment/rim/mesh_k.sh
- environment/rim/scan_t.sh
- environment/bag/skim_p.sh
- environment/bag/note_u.sh
- environment/deck/emit_m.sh
- environment/wire/sock_v.sh
- environment/wire/knit_q.sh
- environment/tools/proxyhealth
- environment/tools/sockprobe
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/config/site_standard.conf
- environment/packaging/backends.sha256
- environment/packaging/README.md
- environment/data/backends/alpha.toml
- environment/data/backends/beta.toml
- environment/data/backends/gamma.toml
- environment/data/backends/delta.toml
- environment/data/backends/epsilon.toml
- environment/data/roster.list
- environment/data/seed/floors.toml
- environment/data/seed/live_floors.toml
- environment/data/seed/leases.toml
- environment/data/seed/journal.jsonl
- environment/data/seed/clock.epoch
- environment/data/seed/abort.d/90-local.cfg
- environment/data/seed/conf.d/10-core.cfg
- environment/data/seed/conf.d/40-lab.cfg
- environment/data/seed/conf.d/90-local.cfg
- environment/data/seed/haproxy.cfg
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rim/mesh_k.sh
  symbol: mesh_k
  kind: function
  signature: mesh_k
  purpose: Lexically fold conf.d server weight keys into effective policy file
- path: ops/axle_n.sh
  symbol: axle_n
  kind: function
  signature: axle_n
  purpose: Apply journal cutover and align tip generations to durable floors
- path: bag/skim_p.sh
  symbol: skim_p
  kind: function
  signature: skim_p
  purpose: Materialize drain leases against desk clock without zeroing weight
- path: ops/helm_r.sh
  symbol: helm_r
  kind: function
  signature: helm_r
  purpose: Rematerialize abort residue unless durable receipt matches
- path: wire/sock_v.sh
  symbol: sock_v
  kind: function
  signature: sock_v
  purpose: Apply folded weights and drain flags to runtime socket state
- path: deck/emit_m.sh
  symbol: emit_m
  kind: function
  signature: emit_m
  purpose: Publish seating ledger JSON from live+durable+socket agreement
```

#### flipping_point_contract

```
locations:
  - id: A
    path: rim/mesh_k.sh
    controls_tests: [test_j2_onyx, test_h8_amber, test_m1_opal, test_w7_quartz]
  - id: B
    path: ops/axle_n.sh
    controls_tests: [test_v5_coral, test_c1_flint, test_m1_opal]
  - id: C
    path: bag/skim_p.sh
    controls_tests: [test_p9_jade, test_u2_mica, test_t4_pearl]
  - id: D
    path: ops/helm_r.sh
    controls_tests: [test_h8_amber, test_c1_flint, test_n4_beryl]
  - id: E
    path: wire/sock_v.sh
    controls_tests: [test_r6_slate, test_u2_mica, test_m1_opal]
  - id: F
    path: deck/emit_m.sh
    controls_tests: [test_q3_topaz, test_r6_slate, test_n4_beryl, test_u2_mica]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: rim/scan_t.sh
  kind: helper
  rhymes_with: mesh_k
  non_fix_purpose: Prints a surface inventory of conf.d filenames for operators
- path: bag/note_u.sh
  kind: helper
  rhymes_with: skim_p
  non_fix_purpose: Appends a non-graded operator note under /var/log/haproxy/
- path: wire/knit_q.sh
  kind: helper
  rhymes_with: sock_v
  non_fix_purpose: Touches a decoy probe stamp under /var/run/haproxy/probe.stamp
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [proxy, seat, backend, backends, drain, drained, weight, generation, socket, fold, conf, lease, haproxy, runtime, schema, applied, receipt, cutover, abort, floor, floors, roster, server, servers]
```
