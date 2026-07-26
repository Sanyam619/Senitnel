# Root Application Monorepo

This tree hosts the root service (`internal.example/rootapp`) and one
in-tree submodule (`internal.example/rootapp/submodule`). Third-party
modules resolve through the file-system proxy under `/app/proxy` and
internal-mirror modules are published to the same proxy for
determinism.

The CI matrix is gated by `/app/bin/matrixci report`, which produces a
JSON verdict across two toolchain profiles (`go1.22`, `go1.23`) and two
build modes (`mod`, `vendor`). Every cell must land at
`status = "ok"` before a merge is accepted.

Pin-floor policy for third-party modules lives at
`/app/docs/security-pin-policy.md`.

Optional tooling imports live in `tools.go` and must stay behind a
`//go:build tools` constraint. The blank import targets
`example.org/toolchain/probe` (or another package under that module),
never the module root path alone.
