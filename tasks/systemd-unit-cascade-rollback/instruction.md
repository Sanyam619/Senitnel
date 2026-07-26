A partial stack cutover left dependency ordering half rewired. /app/scripts/stack-health.sh
lists the target on disk but start attempts on dependent services stall or fail,
/app/scripts/depwalk-wrapper.sh reports unresolved After edges between named pairs, and
/app/scripts/ledger-stub.sh will not emit a rollback report until the graph is reconciled.
Operator notes live under /app/config/; lab binaries under /app/bin/; rebuild sources under
/app/. Fixture anchors shipped with the lab are read-only.

Produce /output/rollback-report.json: version 1, units for stack.target, ingress.service,
cache.service, store.service, journal.service, and relay.service — each with name, state,
start_order, hard_deps, soft_deps. All six must reach active, override merge must follow
the precedence in /app/config/field-notes.md, the graph must be acyclic with a valid start
sequence, and report fields must match per-unit runtime state on disk.
