Operator notes

Cutover runs from /app/ops/run_cutover.sh. That path folds unit policy,
aligns the durable lease and journal plane from the sealed cutover
journal under the active seal cap, resolves preference drop-ins, seats
tenants, arms seal generation, writes a sealed cutover receipt, suppresses
abort-window isolation rematerialize when the receipt matches, then runs
the prebuilt ring materializer and preflight check.

When cutover mode is sealed, the journal seal tip must agree with the
sealed journal tip (epoch and slot prefix together). Incomplete seal tips
that omit the prefix, durable maps that still track harbor, or profile
sheets that drifted past the seal cap, leave the broker ring unable to
register fresh buffers.

Unit-policy fold must clear PrivateMounts isolation drift on the live
unit and every live.d drop-in. Seating tenants into the broker mount tree
alone does not count as that repair. Abort-window fragments rematerialize
isolation unless a matching sealed cutover receipt is present.

Preference fold across /etc/ingest/pref.d/ must leave a seal-bound
effective preference for materialize.

Preflight rematerializes harbor/rollback state when the durable plane,
seal tip, preference, receipt, broker seating, or unit isolation still
disagree. A second preflight on an already-correct lab must leave the
lease map and buffer registry stable and stamp the preflight run as
stable.

Off-roster tip names that survived a crash must not remain in the
activation tip map after a successful cutover pass.

A second invocation of /app/ops/run_cutover.sh after a durable recovery
must succeed without operator hand-edits; recovery that only patches live
files once is not durable.
