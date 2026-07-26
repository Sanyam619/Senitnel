We're mid cutover on the lab host. Cgroup trees under /data/lab/cgroup/ are half moved — topscan on the unified root comes back OK, unit-top.sh lists app-batch.scope, app-worker.scope, and app-api.scope, treewalk flags a v1 shadow on at least one unit, and cutover-stub.sh won't give you a ledger yet.

/opt/lab/config/ has notes and paths. Binaries under /opt/lab/bin/, sources under /opt/lab/src/ for rebuilds. Don't touch /data/fixtures/cgroup-seed/.

Need /output/cutover-report.json at the end: version 1, scopes for all three names, each row carrying name, tree, controllers, io_throttle_events, memory_high_events.

You have to finish the move, not photograph the broken layout. All three scopes land on unified with io and memory in controllers, legacy v1 shadow dirs for those names go away, app.slice gets io and memory delegated, bench tooling fills per-scope accounting files on the unified nodes, and the report counters match those files.
