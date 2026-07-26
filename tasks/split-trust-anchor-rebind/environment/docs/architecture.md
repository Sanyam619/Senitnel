# Edge stack layout

The binary `bin/edgegate` loads on-disk material under `data/`, scores
intermediate slots under `/tmp/edge_slots/`, and emits an admission ledger.
Operators invoke `scripts/run-admit.sh` for a matrix pass and
`scripts/edge-reload.sh` when restore-side material is refreshed.
Surf health is exposed through `scripts/surfcheck`.
