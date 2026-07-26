### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: openldap-syncrepl-consumer-tip-lattice
- Title: LDAP Syncrepl Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["openldap", "syncrepl", "contextcsn", "provider-prefer", "hold-window", "ops-seating"]
- Milestones: 0

### Discovery budget
- Discovery: Prefer.d fold is last-wins lexical; shipped mesh_x is first-wins so early surface decoy sticks.
  Planned location: `/app/rim/mesh_x.sh` + `/etc/ldap/prefer.d/`
  Why instruction must not reveal it: naming first-vs-last wins collapses the prefer locus to a one-line sed.
- Discovery: Durable tip is sealed journal row for gen.target (tip_g7), not newest tip_live CSN crumbs under `/var/lib/ldap/<name>/contextCSN`.
  Planned location: `/var/lib/ldap/ops/csn_journal.jsonl` + `/app/ops/axle_y.sh`
  Why instruction must not reveal it: pointing at tip_live vs tip_g7 makes the journal a checklist.
- Discovery: helm_w writes surface.uri into slapd unless prefer.accept tip equals sealed tip_id; matching receipt applies site_standard providerURI.
  Planned location: `/app/ops/helm_w.sh` + `/var/lib/ldap/ops/prefer.accept`
  Why instruction must not reveal it: naming the receipt field alone without coupling still allows cn=config-only patches that rematerialize undoes.
- Discovery: ldaphealth greensis on entry-count equality, not CSN/prefer/hold agreement.
  Planned location: `/usr/local/bin/ldaphealth` + `/app/rim/scan_m.sh`
  Why instruction must not reveal it: already stated as surface bait; exact count logic is discoverable.

### Anti-trivialization verdict
Hard-only seating lattice with ≥3 discovery items and ≥3 coordinated loci. Not single-artifact repair. Symptoms-only instruction. Re-entry rejects hand-authored JSON.

### Topology enumeration (3 candidate fix topologies)
1. Ops helpers: mesh_x × axle_y × skim_z × helm_w × emit_q/seatctl — no single helper greens all mineral tests.
2. Config authorities: prefer.d fold × csn_journal seal × floors × holds × prefer.accept — editing one authority leaves distant bound cells wrong.
3. Publish path: slapd.d provider rewrite × effective.conf × state tip_*.csn × ledger sync_ok — partial publish fails idempotent/deep cells.

### Rubric axes
Verifiable/Well-specified/Solvable/Difficult/Interesting/Outcome-verified: Pass (live LDAP seating end-state).

### Hardness axes
Discover/Synthesize/Diagnose/Navigate coupling/Reason beyond training: Pass via CSN tip × prefer × hold × rematerialize coupling uncommon in training as a single seating desk.

### Instruction completeness test
Cannot solve from instruction alone — must discover seal tip selection, prefer fold polarity, hold clock compare, and prefer.accept coupling from docs + runtime.

## Reviewer Appendix

### Implementation plan
Broken bash helpers under /app prepare live /etc/ldap + /var/lib/ldap incorrectly. Correct seatctl publishes when helpers prepare durable agreement. Oracle rewrites helpers + prefer.accept + 90-local, then double-runs seating.

### Oracle notes
solve.sh rewrites mesh_x (last-wins), axle_y (sealed tip ≥ floor), skim_z (hold_block when until > clock), helm_w (site URI iff tip match else surface), emit_q→seatctl; sets prefer.accept tip_g7 and site-standard 90-local.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: five helper bodies + prefer.accept + 90-local (~substantive).
Residual hardness: coupled tip×prefer×hold×rematerialize; novel tip inject.
Collapse verdict: PASS

### Naming-pass record
**Instruction nouns extracted:** directory, consumer, replication, schema_tag, consumers, provider, contextCSN, generation, bound, holds, suffix, until_epoch, sync_ok, slapd, durable, prefer, journal, ldaphealth, samples, entrypoint, seating, verifier, syncrepl, rematerialize, floor, tip, decoy, hold, window, roster, lexical, receipt, surface
**Renames during drafting:** None — first-pass naming used opaque mesh_x/axle_y/skim_z/helm_w/emit_q
**Test names audited:** test_q3_topaz, test_n4_beryl, test_w7_quartz, test_j2_onyx, test_v5_coral, test_p9_jade, test_h8_amber, test_c1_flint, test_r6_slate, test_u2_mica, test_m1_opal, test_t4_pearl, test_k5_garnet
**Concentration math:** 13 tests; max location share ≤4/13 ≈ 0.31 < 0.5 PASS
