Ingest lab layout

Live configuration lives under /etc/ingest/. Runtime durable state lives
under /var/lib/ingest/. Operator recovery starts at
/app/ops/run_cutover.sh. Prebuilt tools live under /app/bin/, including
/app/bin/ringfan, /app/bin/preflight, and /app/bin/healthctl. Surface
status is also available via /app/ops/check_surface.sh; surface OK alone
does not mean the cutover is complete.

An active seal cap lives at /etc/ingest/fleet.seal. The sealed cutover
journal under /var/lib/ingest/journal/act.wal records generation-scoped
tips. Tips whose generation exceeds the active seal cap are not part of
the durable plane. Harbor material under /etc/ingest/harbor.toml and the
profile sheet /etc/ingest/fleet.toml may disagree with that sealed tip.

Journal material also includes a cutover mode flag and a seal tip that
must bind the durable epoch to the sealed slot prefix when sealed mode is
active. Preference drop-ins under /etc/ingest/pref.d/ contribute an
effective cutover preference for materialize.

Unit policy for the ingest service is merged from
/etc/ingest/units/live.service, every drop-in under live.d/, and abort-
window fragments under abort.d/. Nested tenant seating requires that
PrivateMounts isolation is not left active across that merged set. A
sealed cutover receipt under /var/lib/ingest/meta/ suppresses abort-
window rematerialize of isolation after a successful pass.

Tenant markers are dual-resident during a broken cutover: they may appear
under the host mount tree and the broker mount tree. A finished cutover
keeps roster tenants under the broker tree only. The active tenant roster
is /etc/ingest/tenant.roster. Tip maps under /var/lib/ingest/meta/ must
follow that roster after a successful pass.

Fixtures under /var/lib/ingest/fixtures/seed are anchors; leave them alone.
