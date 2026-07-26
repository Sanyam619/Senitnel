### Decision
GO — Attempt 1. Original security forensics task on bidirectional byte delivery from captures; distributed Go fix path with opaque symbols.

### Metadata
- version: 2
- Task name: tcp-stream-injection-forensics
- Title: TCP Stream Forensics
- Category: security
- Languages: ["go"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["go", "pcap", "network", "forensics", "security", "tcp"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent runs `/opt/wiretap/bin/wiretap analyze --manifest /opt/wiretap/data/manifest.json --out /output` after fixing the Go reassembly lane under `/opt/wiretap/`. For each flow in the manifest, write `/output/reassembled/<flow_id>_c2s.bin` and `/output/reassembled/<flow_id>_s2c.bin` containing the application bytes each endpoint delivered to userspace, plus `/output/findings.json` version 1 with per-flow `c2s_len`, `s2c_len`, half-open `[start,end)` `c2s_injected` and `s2c_injected` ranges relative to each delivered stream, and `overlap_notes` entries `{rel_off, dir, kept}` where `dir` is `c2s` or `s2c` and `kept` is `earlier` or `later`. Flow ids: `flow_alfa`, `flow_bravo`, `flow_charlie`, `flow_delta`.

### Failure topology
Captures include reordering, duplicate spans with disagreeing octets, holes that close later, and a middlebox that shrinks the advertised window before smaller follow-on slices arrive. The stock analyzer concatenates capture order, ignores window clamping, never compares duplicate spans, and resolves overlaps by earliest timestamp. Symptoms: delivered streams disagree with peer notes, tamper ranges empty when duplicates differ, truncated `flow_delta` output.

### Environment shape
Go module at `/opt/wiretap` with cmd entrypoint, internal packages for scan/stitch/queue/limit/challenge/emit, pkg helpers, manifest and captures under `/opt/wiretap/data`, peer docs under `/opt/wiretap/docs`, config under `/opt/wiretap/config`.

### Required artifacts
instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, solve.sh, test.sh, test_outputs.py, 22+ environment files including Go sources, manifest, pcaps, peer docs, build script.

### Test plan
- test_u1_alfa_c2s_bytes — byte-exact c2s for flow_alfa
- test_k3_alfa_s2c_bytes — byte-exact s2c for flow_alfa
- test_m8_bravo_c2s_keeps_first — bravo c2s resists tamper retrans
- test_p2_bravo_injected_ranges — set equality on bravo c2s injected ranges
- test_q5_charlie_s2c_gap — charlie s2c waits for hole fill
- test_r7_delta_c2s_window — delta c2s respects shrink
- test_s4_findings_schema — findings.json version and keys
- test_t9_overlap_notes_alfa — overlap note present for alfa
- test_h2_overlap_kept_alfa — overlap kept polarity for alfa c2s

### Drafting guardrails
Symptoms-only instruction; no RFC names, no fix-path symbol names matching instruction nouns; expected bytes live in tests only.

### Triviality Ledger
- Capture-order concat passes alfa reorder test but fails gap/window flows because queue and limit modules stay naive.
- First-wins overlap passes alfa duplicates but fails bravo/s2c where peer docs specify later-wins paths.
- Skipping payload compare yields empty injected ranges on bravo despite disagreeing duplicates on wire.

### Per-gate Pitfall Inventory
- RC3: tests compare SHA256 of streams and injected set equality, not existence-only.
- RC6: instruction describes symptoms and output schema, not stitch/queue/limit internals.
- RC7: oracle rewrites four internal modules with substantive merge/drain/clamp/compare logic.
- GX9: instruction names flow ids and field names, not per-byte expected payloads.
- CR7: fix-path symbols use opaque k4/m2/p7/n5 names; no instruction noun substrings.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/Dockerfile
- environment/.dockerignore
- environment/go.mod
- environment/go.sum
- environment/cmd/wiretap/main.go
- environment/internal/scan/reader.go
- environment/internal/scan/reader_test.go
- environment/internal/k4/stitch.go
- environment/internal/k4/hash.go
- environment/internal/m2/queue.go
- environment/internal/m2/slot.go
- environment/internal/p7/limit.go
- environment/internal/p7/clock.go
- environment/internal/n5/challenge.go
- environment/internal/n5/challenge_test.go
- environment/internal/r8/emit.go
- environment/pkg/lane/flow.go
- environment/pkg/lane/flow_test.go
- environment/config/lab.toml
- environment/data/manifest.json
- environment/data/build_captures.py
- environment/data/captures/.gitkeep
- environment/scripts/smoke.sh
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: internal/k4/stitch.go
  symbol: stitch
  kind: function
  signature: func stitch(buf map[int]byte, seq int, payload []byte, ts float64, preferLater bool) map[int]byte
  purpose: merge payload bytes into position map honoring overlap preference
- path: internal/m2/queue.go
  symbol: drain
  kind: function
  signature: func drain(buf map[int]byte, start int) ([]byte, int)
  purpose: emit contiguous bytes from start while present
- path: internal/p7/limit.go
  symbol: ceiling
  kind: function
  signature: func ceiling(rcvNxt int, win int, seq int, length int) bool
  purpose: return whether segment end fits inside receive window
- path: internal/n5/challenge.go
  symbol: compare
  kind: function
  signature: func compare(a []byte, b []byte) (same bool, ranges [][2]int)
  purpose: detect byte ranges where two spans disagree

#### flipping_point_contract
locations:
  - id: A
    path: internal/k4/stitch.go
    controls_tests: [test_u1_alfa_c2s_bytes, test_m8_bravo_c2s_keeps_first, test_t9_overlap_notes_alfa]
  - id: B
    path: internal/m2/queue.go
    controls_tests: [test_q5_charlie_s2c_gap, test_k3_alfa_s2c_bytes]
  - id: C
    path: internal/p7/limit.go
    controls_tests: [test_r7_delta_c2s_window]
  - id: D
    path: internal/n5/challenge.go
    controls_tests: [test_p2_bravo_injected_ranges, test_m8_bravo_c2s_keeps_first]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: internal/k4/hash.go
  kind: helper
  rhymes_with: stitch
  non_fix_purpose: rolling fingerprint for manifest rows
- path: internal/m2/slot.go
  kind: helper
  rhymes_with: drain
  non_fix_purpose: fixed-size slot pool for capture metadata
- path: internal/p7/clock.go
  kind: helper
  rhymes_with: ceiling
  non_fix_purpose: capture timestamp normalization

#### code_forbidden_tokens
code_forbidden_tokens: [packet, capture, pcaps, tcp, sessions, application, protocol, segments, retransmissions, payloads, injection, endpoint, userspace, stream, flows, reassembled, findings, injected, ranges, delivered, overlap, decisions, forensics]
