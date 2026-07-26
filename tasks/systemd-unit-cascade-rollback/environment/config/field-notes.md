# stack lab notes

Live unit bodies sit under `/data/stack/units/`.
Override fragments live under `/data/stack/overrides/<name>.d/*.conf`.
Merged effective keys land in `/data/stack/runtime/<name>/merged.ini`.
Activation state files sit beside them as `state` and `order`.

Drop-in precedence follows numeric prefix ordering: lower numbers apply first,
later numbers override earlier keys for the same section.

Diagnostic helpers: `/app/scripts/stack-health.sh`, `/app/scripts/depwalk-wrapper.sh`,
`/app/scripts/ledger-stub.sh`.

Anchor snapshots under `/data/fixtures/stack-seed/` are read-only.

Rebuild lab binaries from `/app` after source edits:
`cargo build --release --offline` then copy artifacts into `/app/bin/`.
