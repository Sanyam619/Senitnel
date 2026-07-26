### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: powerdns-authoritative-zone-tip-lattice
- Title: PowerDNS Zone Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["powerdns", "zone-serial", "backend-prefer", "pdns-fold", "generation-gate", "ops-journal"]
- Milestones: 0

### Discovery budget
- Discovery: The authoritative journal batch is the latest sealed+complete batch at gen.target; an earlier same-gen revision is superseded and an incomplete gen-9 batch is bait
  Planned location: /var/lib/powerdns/ops/zone_journal.jsonl + lath_p
  Why instruction must not reveal it: naming latest-batch/complete selection collapses tip resolve to transcription
- Discovery: The selected backing store is the highest-epoch registry binding not present in the retirement ledger; the newest row is retired and matches the live sqlite decoy
  Planned location: store_registry.jsonl + retired_stores.jsonl + gaff_s
  Why instruction must not reveal it: naming the resolution rule or the winning store is an answer key
- Discovery: Record holds pin two records to non-tip content; a correct seat reports honored=false for exactly those rows while seat_ok stays true
  Planned location: ops/holds.jsonl + moor_w + flue_d
  Why instruction must not reveal it: listing held rows collapses honor polarity
- Discovery: mesa floor 8 rejects gen 7; live floors are decoys; fold aborts quarry via 40-lab while 90-local abort residue vanishes after site-standard install
  Planned location: durable floors vs /etc/powerdns/floors + pdns.d fold
  Why instruction must not reveal it: naming zones collapses floor/abort polarity
- Discovery: Surface rematerialize (keel_x) rewrites tips/sheets/serials every pass until prefer is durable AND bind gen equals gen.target
  Planned location: wire/keel_x.sh + ops/prefer.toml + tip_bind.accept
  Why instruction must not reveal it: instruction states the outcome (live/surface preference keeps surface materials in play) but not the gate mechanics

### Anti-trivialization verdict
Checks 1–21 addressed via coupled receipt×tip×fold×store×honor×surface-gate seating; not policy-knob transcription; not independent polarity stubs alone (surface rematerialize undoes naive sheet edits; store cells fail after serial fixes; honor cells fail flip-all); discovery budget ≥5; topologies ≥3; symptoms-only instruction.

### Topology enumeration (3 candidate fix topologies)
1. Receipt-first: crib_j + lath_p + flue_d state; receipt alone insufficient without tip apply and site-standard install
2. Tip-first: lath_p + keel_x + moor_w; correct tips still clobbered by ungated surface copy and unpublished without sheet/serial writes
3. Store-first: gaff_s + moor_w + lath_p; correct store fails publish cells until serials match tip and fold abort excludes quarry

### Rubric axes
Verifiable Pass; Well-specified Pass; Solvable Pass; Difficult Pass; Interesting Pass; Outcome-verified Pass.

### Hardness axes
- Discover: journal batch selection, registry retirement, holds, floor polarity, receipt format all live in env ledgers/runtime behavior
- Synthesize: report correctness spans ops/, rig/, span/, wire/ helpers plus two durable config surfaces
- Diagnose: instruction gives drift symptoms; agents must find why publish/honor/backends stay wrong across reseats
- Navigate coupling: fixing serials without prefer/bind gate is undone by rematerialize; fixing store without sheets fails publish; flip-all honored fails holds
- Reason beyond training: superseded same-gen revision + retirement-aware store resolution + mixed honored polarity are not textbook recipes

### Instruction completeness test
No — the instruction names symptoms, the entrypoint, the report path/vocabulary, and receipt/site-standard outcomes; every graded value (serials, store, honored rows, abort set, floors) must be derived from durable ledgers and runtime behavior.

## Reviewer Appendix

### Implementation plan
Ops desk seats five authoritative zones. Live `/etc/powerdns` (pdns.conf, pdns.d drop-ins, zones.d record/store sheets, serial sheets, decoy floors) drifted from durable authority under `/var/lib/powerdns` (prefer mode, sealed zone journal, store registry + retirements, holds, floors, abort package, surface materials). Broken helpers: crib_j (unconditional abort rematerialize + receipt delete), lath_p (stamps tips from live sheets, never applies journal or writes receipt/bind/site tokens), gaff_s (newest-any registry row → retired sqlite decoy), moor_w (publishes all, honors all, writes no sheets), keel_x (unconditional surface clobber). Correct: vane_t (fold), flue_d (deep self-audit emitter). Oracle rewrites the five helpers plus prefer mode and reseats twice.

### Oracle notes
solve.sh: prefer.toml → durable; crib_j gains receipt gate; lath_p resolves latest sealed complete gen-7 batch, writes tip serial/gen/records per zone, gen.live, tip_bind.accept, installs site-standard live 90-local, writes cutover.ok; gaff_s resolves highest-epoch non-retired store; moor_w writes apex+record sheets (holds applied), serial and store sheets, publish set (serial∧floor∧store∧¬abort), honor set (live==tip); keel_x gates surface copy on durable prefer + bind gen; run entrypoint twice.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch: rewrite five helper bodies + flip prefer mode — substantive multi-file bash/python logic, not deletions.

Likely editable frontier: ops/crib_j.sh, ops/lath_p.sh, rig/gaff_s.sh, span/moor_w.sh, wire/keel_x.sh, /var/lib/powerdns/ops/prefer.toml

Requirement-to-file map: not 1:1 — published requires lath_p+gaff_s+moor_w+vane_t outputs; honored requires lath_p+moor_w+holds; byte-identical requires crib_j+lath_p receipt loop; recovery requires keel_x gate.

Oracle estimated complexity: ~200 lines non-boilerplate.

Red flags: emitter contains expected-state comparison (mirrors squid emit_m; accepted precedent — it never re-resolves journal/registry).

Residual hardness: even with the file tree visible, agents must decode the journal supersession rule, the retirement-aware store pick, holds polarity, and the rematerialize gates from ledger contents and reseat behavior; naive fixes are rewritten every pass.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:** powerdns, dns, zone, serial, backend, store, sqlite, journal, tip, generation, floor, record, hold, honored, published, prefer, durable, live, surface, seat, abort, cutover, receipt, health, fixture, roster, fold, schema, ledger, registry, retirement

**Renames during drafting:**
- None — first-pass naming was already clean against the forbidden list (crib_j, lath_p, vane_t, gaff_s, moor_w, keel_x, flue_d, scan_y, lace_n, note_g)

**Test names audited:**
- test_k4_agate
- test_r7_basalt
- test_d2_gypsum
- test_v9_chert
- test_m3_pumice
- test_j6_schist
- test_p5_marble
- test_t8_gneiss
- test_c6_shale
- test_w1_borax
- test_h9_norite
- test_e2_talc
- test_a5_ochre
- test_u4_gabbro
- test_y7_umber
- test_g3_lignite

**Concentration math:**
- Total tests across `flipping_point_contract`: 11 distinct
- Per location:
  - A (`ops/crib_j.sh`): 2/11 = 0.18
  - B (`ops/lath_p.sh`): 3/11 = 0.27
  - C (`rig/gaff_s.sh`): 1/11 = 0.09
  - D (`span/moor_w.sh`): 3/11 = 0.27
  - E (`wire/keel_x.sh`): 2/11 = 0.18
- Cap: 0.5. Max ratio observed: 0.27. Status: PASS

### Per-test feasibility pre-check
- Test: test_k4_agate — schema/seat_ok/published polarity; 2+ approaches; not chain-dependent (reseat sets own state); LOW
- Test: test_r7_basalt — byte-identical double seat; 2+; LOW
- Test: test_d2_gypsum — frozen fixture/apex alignment; 2+; LOW
- Test: test_v9_chert — supersession serials derived from journal; 2+; LOW
- Test: test_m3_pumice — incomplete gen not applied; 2+; LOW
- Test: test_j6_schist — store resolution derived from registry+retirements; 2+; LOW
- Test: test_p5_marble — floor gate; 2+; LOW
- Test: test_t8_gneiss — fold abort; 2+; LOW
- Test: test_c6_shale — forensic abort vs site tokens; 2+; LOW
- Test: test_w1_borax — receipt semantics + poisoned re-entry; 2+; MEDIUM (documented in instruction/docs)
- Test: test_h9_norite — holds honored polarity; 2+; MEDIUM (documented in docs)
- Test: test_e2_talc — live sheets carry tips; 2+; LOW
- Test: test_a5_ochre — serving bait; 2+; LOW
- Test: test_u4_gabbro — state+/output wipe re-entry; 2+; LOW
- Test: test_y7_umber — prefer flip poison/recover; 2+; MEDIUM (docs state surface materials stay in play while preference is live)
- Test: test_g3_lignite — full matrix equality vs derived EXPECTED; 2+; LOW
