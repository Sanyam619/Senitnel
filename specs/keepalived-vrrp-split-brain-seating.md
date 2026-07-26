### Decision
GO — Attempt 4 (taxonomy redesign). Hard `system-administration` task. Prior
shape graded rewriting algorithmic Bash under `/app` (debugging primary
activity). Redesign ships correct prebuilt `/app/publisher/vrrpseat` and puts
the frontier in broken `/app/ops/` helpers that materialize live `/etc` +
`/var` tables (abort window, conf.d fold, sealed prefer tip, UP-only track
weights, hold/floor/netif eligibility, event-id transition scrub). Instruction
is scenario/outcome prose. Novel couplings: track status polarity, netif
generation floors, deep `advert.map` vs surface MASTER-OK bait.

### Metadata
- version: 2
- Task name: keepalived-vrrp-split-brain-seating
- Title: Keepalived VRRP Split-Brain Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["keepalived", "vrrp", "split-brain", "priority-fold", "transition-journal", "generation-gate"]
- Milestones: 0

## Authoring Brief

### Public contract
The task operates live Keepalived state under `/etc/keepalived/` and durable
operations state under `/var/lib/keepalived/ops/`. Running
`/app/ops/run_vrrp_seat.sh` writes `/output/vrrp-seat.json`. The document has
`schema_tag` (string), `instances` (array of `{name:string, vrid:integer,
state:string, priority:integer, vip:string, generation:integer}`),
`transitions` (array of `{vrid:integer, epoch:integer, from:string,
to:string}`), and `seat_ok` (boolean).

For each VRID, at most one eligible peer may hold MASTER. Eligibility requires
the durable generation floor and an inactive hold. Effective priority comes
from the complete lexical conf.d fold. The winner is the durable maximum;
durable preference resolves equal maxima. A committed, unretracted movement
away from MASTER vetoes an otherwise valid winner for that VRID; retractions
bind to event ids. Different VRIDs may legitimately have different MASTER
peers. Frozen `/app/data/vrrp/` peer fixtures stay intact. The health command is
surface-only. Repeated entrypoint runs produce byte-identical output.

### Failure topology
The shipped desk has six interacting authority boundaries. The live conf.d
fold mishandles scoped replace/delta records. Preference selection consumes an
incomplete later batch instead of the latest complete sealed generation.
Eligibility reverses one hold boundary and admits below-floor peers. Transition
reduction treats retraction as a VRID-wide clear rather than an event-id
cancellation. A saved abort sheet rematerializes before every fold unless a
generation-bound receipt matches. The publisher trusts current MASTER tokens
and therefore accepts split brain while missing legitimate independent masters
on different VRIDs.

The entrypoint sequences those components. A local edit to current state is
not durable: rematerialization and the next fold can undo it. Conversely, a
receipt-only change preserves stale election and history behavior. Dynamic
tests add a peer and a committed transition batch so fixed baseline tables do
not satisfy the task.

### Environment shape
- Live Keepalived configuration under `/etc/keepalived/` with ordered drop-ins.
- Durable preference, transition, hold, floor, generation, abort, and receipt
  state under `/var/lib/keepalived/ops/`.
- Distributed Bash components under `/app/plane`, `/app/state`, `/app/guard`,
  `/app/history`, and `/app/emit`, orchestrated by `/app/ops`.
- Genuine surface helpers under `/app/cli`, `/app/plane`, `/app/state`, and
  `/app/history` that support operator views without deciding deep seating.
- Immutable peer inputs under `/app/data/vrrp/`, packaging pins, and concise
  format/operator documentation.

### Required artifacts
Create the standard single-step layout with `instruction.md`, `task.toml`,
`output_contract.toml`, `environment/`, `solution/solve.sh`, and
`tests/{test.sh,test_outputs.py}`. The environment is Bash-only, has more than
20 substantive files, includes `.dockerignore`, and installs hashed verifier
dependencies in the Dockerfile. No compose stack, runtime downloads, build
artifacts, answer files, or AI-scaffolding names.

### Test plan
- `test_q3_topaz`: recomputes the full baseline instance ledger, validates all
  schema types in the same domain assertion, and rejects duplicate MASTER for a
  VRID.
- `test_n4_beryl`: runs the full entrypoint twice and checks byte identity plus
  unchanged live/durable convergence.
- `test_w7_quartz`: pins frozen peer fixtures, stages an additional peer outside
  the frozen tree, and requires the same general fold/election path to seat it.
- `test_v5_coral`: checks latest complete sealed preference selection against
  an incomplete later batch and generation floors.
- `test_p9_jade`: covers active, boundary, and expired hold windows across
  different VRIDs while checking winner changes rather than hold-file format.
- `test_h8_amber`: verifies abort-package preservation, live drop-in
  rematerialization suppression, and effective priorities after a second run.
- `test_c1_flint`: checks the generation-bound receipt and proves that changing
  the target generation re-enables saved-sheet application until reseated.
- `test_r6_slate`: checks two simultaneous MASTER instances on different VRIDs
  and no same-VRID split brain.
- `test_u2_mica`: reconstructs committed transition events and event-id
  retractions from interleaved batches.
- `test_m1_opal`: checks the full eligibility × effective-priority × durable
  tie-preference matrix, including a held high-priority peer.
- `test_k5_garnet`: proves that retracting one movement does not clear a second
  active movement for the same VRID.
- `test_s8_zircon`: removes output and derived tables, re-enters the operator
  path, and compares a fresh independent reconstruction.
- `test_t4_pearl`: confirms surface MASTER-OK is insufficient by coupling it to
  the deep ledger and live single-master invariant.
- `test_b6_cobalt`: injects scoped replace and delta records whose lexical order
  changes two candidate rankings and checks both VRIDs.
- `test_d4_jet`: injects a new sealed generation with an equal-priority tie,
  below-floor peer, and hold boundary.
- `test_x7_agate`: injects interleaved movement/retraction rows, including a
  retraction naming an event on another VRID, and checks continuity.

All tests grade computed admin outcomes and allow multiple implementation
approaches. Scenario-mutating tests snapshot and restore their own state and do
not depend on execution order.

### Drafting guardrails
Keep the instruction human and outcome-focused, without repair/debug framing,
fix locations, exact baseline winners, selected batch ids, or a transition
answer table. Do not put intent comments on oracle-touched scripts. Test names
remain opaque. Expected values are reconstructed in tests from private logic,
not stored in environment files. No standalone schema, existence, health, or
fixture-integrity scoring cell: each such assertion is coupled to substantive
VRRP behavior.

### Triviality Ledger
- Hand-written JSON fails because tests clear output and derived tables before
  invoking the entrypoint.
- Editing current MASTER tokens fails because the full ledger is reconstructed
  from folded live config, durable peer selection, eligibility, and history.
- Raising one peer priority fails different-VRID independent-master cases and
  dynamic lexical fold cases.
- Choosing the last preference row fails because the newest batch is
  incomplete; only a complete sealed generation is authoritative.
- Clearing all transition rows fails active movement cases; clearing by VRID
  fails event-id cross-retraction cases.
- Deleting the saved abort sheet fails forensic preservation; deleting the live
  drop-in fails stable re-entry and effective-priority checks.
- Hardcoding baseline winners fails novel peer, new generation, tie, hold, and
  interleaved transition injections.

### Per-gate Pitfall Inventory
- RC1: the oracle adds general parsing and reconciliation logic rather than
  deleting checks or reverting one setting.
- RC2: fix-path names are opaque; no broken/golden/expected naming.
- RC3: every test computes election, continuity, or re-entry behavior; no
  format-only cell.
- RC4: expected outcomes are verifier-owned and dynamic injections prevent
  mutable reference bypasses.
- RC5: no answer-shaped ledger or selected-winner fixture is solver-visible.
- RC6: the instruction gives the operational contract without causes, baseline
  winner values, fix paths, or implementation steps.
- RC7: substantive oracle delta spans six Bash components and exceeds 80 lines.
- CR1/CR2: use the committed symbols and six-location concentration map
  verbatim.
- CR3/CR7: fix-path symbols, parameters, paths, and test names avoid instruction
  nouns.
- CR8: no single orchestrator names more than two fix-path symbols directly;
  phase discovery uses a neutral run list.
- CR9/GX7/GX8: all asserted schema/value vocabulary has an instruction or
  environment home; tests use only standard infrastructure imports.
- GX1/GX3/GX4: no intent comments, cosmetic edits, or no-op rewrites in the
  oracle.
- GX5/GX6/GX9/GX10: no answer recital, causal walkthrough, or ambiguous
  polarity prose.
- Static/platform: `allow_internet=false`, Bash language roster, hashed
  requirements, explicit `check=` for subprocess calls, PLR0124-clean finite
  checks, pinned image/packages, and packaged `.dockerignore`.
- Category: primary graded activity remains live `/etc` and `/var` Keepalived
  administration through the named operator entrypoint.

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
- environment/ops/run_vrrp_seat.sh
- environment/ops/run.list
- environment/plane/fold_h.sh
- environment/plane/list_n.sh
- environment/state/choice_m.sh
- environment/state/mirror_s.sh
- environment/guard/hold_c.sh
- environment/guard/window_c.sh
- environment/history/trace_p.sh
- environment/history/view_b.sh
- environment/emit/report_y.sh
- environment/lib/kv.sh
- environment/lib/json.sh
- environment/cli/vrrphealth
- environment/cli/seatview
- environment/docs/weight-format.md
- environment/docs/journal-format.md
- environment/docs/operator-notes.md
- environment/config/site_policy.conf
- environment/packaging/vrrp.sha256
- environment/data/vrrp/peer_a.conf
- environment/data/vrrp/peer_b.conf
- environment/data/vrrp/peer_c.conf
- environment/data/vrrp/peer_d.conf
- environment/data/vrrp/peer_e.conf
- environment/data/vrrp/peer_f.conf
- environment/seed/etc/keepalived/keepalived.conf
- environment/seed/etc/keepalived/conf.d/10-base.conf
- environment/seed/etc/keepalived/conf.d/30-zone.conf
- environment/seed/etc/keepalived/conf.d/60-weights.conf
- environment/seed/etc/keepalived/conf.d/90-local.conf
- environment/seed/var/lib/keepalived/ops/prefer.jsonl
- environment/seed/var/lib/keepalived/ops/transitions.jsonl
- environment/seed/var/lib/keepalived/ops/holds/peer_b.hold
- environment/seed/var/lib/keepalived/ops/holds/peer_e.hold
- environment/seed/var/lib/keepalived/ops/floors/peer_a.floor
- environment/seed/var/lib/keepalived/ops/floors/peer_b.floor
- environment/seed/var/lib/keepalived/ops/floors/peer_c.floor
- environment/seed/var/lib/keepalived/ops/floors/peer_d.floor
- environment/seed/var/lib/keepalived/ops/floors/peer_e.floor
- environment/seed/var/lib/keepalived/ops/floors/peer_f.floor
- environment/seed/var/lib/keepalived/ops/state/generation.target
- environment/seed/var/lib/keepalived/ops/state/generation.live
- environment/seed/var/lib/keepalived/ops/state/clock.epoch
- environment/seed/var/lib/keepalived/ops/state/cutover.ok
- environment/seed/var/lib/keepalived/ops/abort.d/90-local.conf

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: plane/fold_h.sh
  symbol: fold_h
  kind: function
  signature: fold_h
  purpose: Merge ordered configuration records into an effective peer table
- path: state/choice_m.sh
  symbol: choice_m
  kind: function
  signature: choice_m
  purpose: Select a committed batch and materialize candidate rows
- path: guard/hold_c.sh
  symbol: hold_c
  kind: function
  signature: hold_c
  purpose: Annotate candidate rows from time-window and floor inputs
- path: history/trace_p.sh
  symbol: trace_p
  kind: function
  signature: trace_p
  purpose: Reduce committed event and cancellation rows into active movements
- path: guard/window_c.sh
  symbol: window_c
  kind: function
  signature: window_c
  purpose: Apply or suppress a saved configuration sheet based on durable state
- path: emit/report_y.sh
  symbol: report_y
  kind: function
  signature: report_y
  purpose: Write deterministic JSON from prepared tables and live files
```

#### flipping_point_contract
```
locations:
  - id: L1
    path: plane/fold_h.sh
    controls_tests: [test_q3_topaz, test_w7_quartz, test_h8_amber, test_b6_cobalt]
  - id: L2
    path: state/choice_m.sh
    controls_tests: [test_v5_coral, test_r6_slate, test_d4_jet]
  - id: L3
    path: guard/hold_c.sh
    controls_tests: [test_p9_jade, test_m1_opal, test_d4_jet]
  - id: L4
    path: history/trace_p.sh
    controls_tests: [test_u2_mica, test_k5_garnet, test_x7_agate]
  - id: L5
    path: guard/window_c.sh
    controls_tests: [test_h8_amber, test_c1_flint, test_n4_beryl]
  - id: L6
    path: emit/report_y.sh
    controls_tests: [test_q3_topaz, test_s8_zircon, test_t4_pearl, test_b6_cobalt]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: plane/list_n.sh
  kind: helper
  rhymes_with: fold_h
  non_fix_purpose: Build a surface inventory consumed by the health command
- path: state/mirror_s.sh
  kind: helper
  rhymes_with: choice_m
  non_fix_purpose: Refresh a non-authoritative operator display from live files
- path: history/view_b.sh
  kind: helper
  rhymes_with: trace_p
  non_fix_purpose: Format recent journal rows for the seatview command
- path: cli/vrrphealth
  kind: surface-tool
  rhymes_with: report_y
  non_fix_purpose: Report current MASTER tokens without durable history checks
```

#### code_forbidden_tokens
```
["keepalived", "vrrp", "split", "brain", "seat", "virtual", "IP",
 "failover", "desk", "output", "schema", "tag", "instances", "array",
 "name", "vrid", "state", "priority", "vip", "generation", "transitions",
 "epoch", "boolean", "MASTER", "peer", "weight", "configuration", "durable",
 "floor", "hold", "journal", "event", "retraction", "health", "fixtures",
 "entrypoint", "JSON"]
```
