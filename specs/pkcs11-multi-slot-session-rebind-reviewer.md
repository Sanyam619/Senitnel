### Decision
GO — Attempt 1. Security cutover (no repair/debug framing), distributed across wire/hold/stamp Java loci, opaque op_a/op_b/op_c, false-green findscan, soft-token multi-slot session semantics.

### Metadata
- Task name: pkcs11-multi-slot-session-rebind
- Title: PKCS#11 Multi-Slot Session Rebind
- Category: security
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["pkcs11", "java", "hsm", "sessions", "slots", "crypto"]
- Milestones: 0

### Discovery budget
- Discovery: After restore, duplicate key labels exist on archive and live slots; the provider currently binds the archive slot id while findscan still counts objects on both.
  Planned location: environment/wire/OpA.java, environment/cmd/findscan, environment/data/token/
  Why instruction must not reveal it: Naming the archive-vs-live bind and that findscan is count-only collapses diagnose and discoverability.

- Discovery: PIN-cached login state outlives the posted ttl_sec across simulated fork/reload unless op_b refreshes session lineage independently of object handles.
  Planned location: environment/hold/OpB.java and environment/data/token/sessions/
  Why instruction must not reveal it: Stating flush-before-reuse order turns the task into a recipe checklist.

- Discovery: Cert identity must re-anchor by label on the live slot after handle reclaim; stale handles remain findable via offline scan but must fail handle_valid authorization.
  Planned location: environment/stamp/OpC.java and environment/lib/HandleMap.java
  Why instruction must not reveal it: Telling solvers handle vs label split removes the coupling that makes partial fixes fail.

### Anti-trivialization verdict
All 21 checks PASS. Residual hardness is disagreeing PKCS#11 authorities (slot bind, session/PIN freshness, cert handle vs label) after adversarial restore, with findscan as verifier bait. Not repair/debug checklist; cutover completion across three opaque Java loci. Distinct from signed-JAR policy rebind and TPM/PCR tasks — soft-token multi-slot session semantics.

### Topology enumeration (3 candidate fix topologies)
- T1: Provider-bind → session PIN policy → cert stamp emit. Locations: OpA, OpB, OpC. Bind alone leaves stale PIN and archive cert handles.
- T2: Session freshness → bind → identity stamp. Locations: OpB, OpA, OpC. PIN flush without live bind still authorizes archive lane.
- T3: Cert re-anchor → bind → session policy. Locations: OpC, OpA, OpB. Label moves without bind/PIN leave archive sessions and outlived login.

### Rubric axes
- Verifiable: PASS — deterministic JSON + authcheck.
- Well-specified: PASS — output schema and outcomes named.
- Solvable: PASS — expert hours with soft-token lab.
- Difficult: PASS — multi-authority PKCS#11 freshness.
- Interesting: PASS — real HSM/soft-token rotation economics.
- Outcome-verified: PASS — grades authorization results.

### Instruction completeness
PASS — symptoms-only; instruction alone insufficient.

### Attack path
Probe soft-token → complete op_a → op_b → op_c emit → authcheck.

### Smallest plausible patch
Three opaque Java cutover methods across wire/hold/stamp; ≥30 LOC; not one keystore edit.

### Collapse audit
PASS — distributed loci, opaque names, findscan bait, decoys LabelPick/CacheKeep.
Residual hardness: slot × session × cert coupling after restore.
Red flags: none.
