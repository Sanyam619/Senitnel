### Decision
GO — Attempt 1. Original Go security forensics task; symptoms-only instruction; distributed fix across k4/m2/p7/n5/r8.

### Metadata
- Task name: tcp-stream-injection-forensics
- Title: TCP Stream Forensics
- Category: security
- Languages: ["go"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["go", "pcap", "network", "forensics", "security", "tcp"]
- Milestones: 0

### Discovery budget
- Discovery: North vs south peer disagree on contested duplicate-span handling (first vs later body).
  Planned location: `/app/docs/peer_north.md`, `/app/docs/peer_south.md`
  Why instruction must not reveal it: naming the rule collapses bravo/s2c asymmetry to a single policy knob.
- Discovery: Middlebox shrink timestamps/bytes in manifest gate acceptance after rewrite.
  Planned location: `/app/data/manifest.json` fields `window_shrink_ts`, `window_shrink_bytes`
  Why instruction must not reveal it: would pinpoint flow_delta fix to manifest-driven window clamp only.
- Discovery: Overlap resolution uses capture timestamp ordering, not capture file order.
  Planned location: broken `internal/k4/stitch.go` vs peer docs
  Why instruction must not reveal it: stating timestamp precedence removes overlap diagnosis.

### Collapse audit
Stage: post-build

Smallest plausible successful patch: Patch stitch/drain/ceiling/compare and wire r8 assemble path — still requires reading both peer docs and manifest shrink metadata.

Likely editable frontier: internal/k4, internal/m2, internal/p7, internal/n5, internal/r8

Collapse verdict: PASS

### Naming-pass record
Instruction nouns extracted: packet, capture, sessions, application, protocol, segments, injection, endpoint, userspace, stream, flows, forensics

Test names audited: test_u1_alfa_c2s_bytes, test_k3_alfa_s2c_bytes, test_m8_bravo_c2s_keeps_first, test_p2_bravo_injected_ranges, test_q5_charlie_s2c_gap, test_r7_delta_c2s_window, test_s4_findings_schema, test_t9_overlap_notes_alfa
