### Decision
GO — Attempt 1. Hard system-administration nftables ruleset seating cutover with coupled fragment fold × abort exclusion × durable prefer × atomic apply × round-trip dump × generation floors. No application-debug / repair frontier.

### Metadata
- Task name: nftables-ruleset-generation-cutover
- Title: Nftables Ruleset Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["nftables", "ruleset-fold", "atomic-apply", "base-chain", "generation-gate", "ops-journal"]
- Milestones: 0

### Discovery budget
- Discovery: Durable prefer sheet under `/var/lib/nft/ops/prefer.conf` owns base-chain policies; surface prefer in `/etc/nft/` is bait.
  Planned location: `/var/lib/nft/ops/prefer.conf` + `ops/pin_m.sh` body polarity
  Why instruction must not reveal it: Naming the prefer path + "use durable not surface" collapses one locus to a one-line sed.

- Discovery: Abort package rematerializes into live `90-local.nft` unless `cutover.ok` has `gen=<target>` and `mode=seal`; matching receipt skips copy but live file must stay site-standard.
  Planned location: `/var/lib/nft/ops/abort.d/` + `ops/helm_w.sh` + docs seating_contract
  Why instruction must not reveal it: Pasting the receipt recipe turns seating into a two-file checklist.

- Discovery: Sealed journal tip for `gen.target` drives table generations; tip below durable floor excludes that table's fragment from the fold.
  Planned location: journal.jsonl + floors + `rim/fold_k.sh`
  Why instruction must not reveal it: Publishing the tip/floor matrix is an answer key for tables/chains.

- Discovery: Atomic apply is flush-then-load; additive `-f` inflates `rules_applied` on re-entry; round-trip requires `applied.nft` to match fold.
  Planned location: `bag/swap_r.sh` + `ops/echo_t.sh` + nft shim
  Why instruction must not reveal it: Naming flush+compare removes the diagnose/synthesize work.

### Anti-trivialization verdict
Checks 1–21 PASS for hard seating cutover: symptoms-only instruction, multi-locus ops authority, re-entry verifier, no single-artifact repair, ≥3 discoveries, ≥3 topologies, not in-distribution "write nft.conf from scratch."

### Topology enumeration (3 candidate fix topologies)
1. **Fold-first:** fold_k × helm_w × pin_m must agree before swap/echo; fixing only fold still fails prefer and round-trip cells.
2. **Apply-first:** swap_r × echo_t × card_w couple atomic load to dump equality and seat_ok; fixing only emit leaves inflate/round-trip red.
3. **Receipt-first:** helm_w × fold_k × pin_m — without matching cutover.ok, abort rematerialize undoes site-standard 90 and prefer pins.

### Rubric axes
- Verifiable: Pass — deterministic nft shim + JSON ledger.
- Well-specified: Pass — schema + seating outcomes in docs.
- Solvable: Pass — expert ops engineer in a few hours.
- Difficult: Pass — coupled authorities, not checklist.
- Interesting: Pass — real firewall seating cutover value.
- Outcome-verified: Pass — grade end-state, not process.

### Hardness axes
- Discover: prefer path, journal seal tip, abort receipt semantics.
- Synthesize: fold × prefer × apply × dump × emit.
- Diagnose: symptoms (seat_ok false, fwhealth active) not causes.
- Navigate coupling: local fragment edit undone by helm rematerialize.
- Reason beyond training: generation-gated fragment fold + round-trip, not textbook nft howto.

### Instruction completeness test
No — instruction alone does not name prefer path, tip/floor matrix, abort receipt keys, or flush semantics. Solver must read docs + durable state + helper behavior.

## Reviewer Appendix

### Implementation plan
Ship broken bash helpers that prepare live nftables.d, prefer, and apply via a file-backed nft shim. Oracle rewrites fold/prefer/apply/dump/helm/emit and writes matching cutover.ok + site-standard 90-local. Tests re-enter seating and compute EXPECTED from durable fixtures.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥20 env files).

### Oracle notes
Rewrite live 90-local to site-standard; write cutover.ok; replace fold_k (lex concat, skip under-floor + abort), pin_m (durable prefer), swap_r (flush+-f), echo_t (list→applied), helm_w (skip rematerialize on receipt), card_w (delegate seatctl). Run entrypoint twice.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: coordinated rewrite of six helpers + receipt + live 90.
Likely editable frontier: rim/fold_k, ops/{pin_m,helm_w,echo_t}, bag/swap_r, deck/card_w, cutover.ok, 90-local.nft
Oracle estimated complexity: ~120 non-boilerplate LOC
Red flags: none if docs stay outcome-level
Residual hardness: generation×abort×prefer×atomic×round-trip coupling
Collapse verdict: PASS

### Naming-pass record
**Instruction nouns extracted:** packet-filter, desk, surface, fwhealth, active, seating, fixtures, integrity, operator, docs, schema_tag, tables, family, name, generation, chains, table, policy, hook, priority, rules_applied, seat_ok, fragment, fold, abort, prefer, decoy, ruleset, round-trip, durable, entrypoint
**Renames during drafting:** None — first-pass naming used opaque fold_k/pin_m/swap_r/echo_t/helm_w/card_w
**Test names audited:** test_q3_topaz, test_n4_beryl, test_w7_quartz, test_j2_onyx, test_v5_coral, test_p9_jade, test_h8_amber, test_c1_flint, test_r6_slate, test_u2_mica, test_m1_opal, test_t4_pearl
**Concentration math:** Total unique tests 12; max location E 4/12=0.33; Cap 0.5 PASS

### Per-test feasibility pre-check
All twelve: valid approaches 2+ (any correct seating), chain-dependent no, feasibility LOW–MEDIUM.
