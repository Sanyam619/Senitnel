Adjacency exports are JSON objects with a peer name and a routes array.
Each route row carries prefix, next_hop, as_path, local_pref, med, and origin.
Scenario manifests list peers and relative rib paths.
Each bundle also ships roa.json (attestation rows) and quarantine.json (export-policy holds).

fib.json maps each bundle id to an ordered list of chosen routes, each row carrying prefix, peer, next_hop, and as_path.

leaks.json wraps an items array. Each item names prefix, peer, and as_path of a stock-admission winner whose peer or as_path differs from the corrected-admission winner for the same prefix. Prefixes where both passes agree, or where stock admits nothing, are omitted. Items are ordered by prefix then peer ascending. The stock baseline is a fixed reference in the report layer and must not be modified.

Corrected admission is the composition of ROA validation, revocation freshness, and quarantine holds; the operative rules and their exact edge-case semantics are the ones already encoded in the Go sources under `internal/guard` (ROA and quarantine tables load from `roa.json` and `quarantine.json`; policy.toml supplies `local_as` and neighbor knobs). A route is admitted only when every rule admits it, and the corrected FIB then selects the surviving route per prefix using the pre-existing tie-break policy.

Converge accepts --policy, --scenarios, and --out. The verifier rebuilds `bin/converge` from the shipped Go module before running it, so the checked deliverable is the Go implementation under `/opt/bgplab` (packages such as internal/guard, internal/ingest, and internal/report). Any repair that yields correct `fib.json` and `leaks.json` from the shipped inputs is accepted; the report layer and the stock baseline pass are the fixed reference.

