# Security Pin Policy

This document catalogs the resolution constraints enforced across every
cell of the `matrixci report` CI harness. Effective resolved versions
outside of any declared constraint below cause the affected CI cell to
reject with a diagnostic that names the axis that was violated.

Fork-based replacement is permitted so long as the *effective resolved
version* the harness reports meets every constraint documented here, and
the replaced module is not listed in the prohibited-replacements table.
Modules listed under retained fork replacements are an exception: those
replace directives are permanent invariants and must not be dropped to
clear a toolchain, vendor, or floor diagnostic.

## Version windows

Every guarded module carries a floor version and a maximum version. The
effective selection must satisfy `floor <= selected <= max`. Selections
above the max are treated identically to selections below the floor.
Within the window, the effective selection must advance to the
**highest non-retracted, non-excluded version** that is at or above the
floor and at or below the maximum. A lower in-window candidate does
not satisfy this rule even when it is also non-retracted and
non-excluded.

| Module                | Floor version | Max version | Advisory reference        |
|-----------------------|---------------|-------------|---------------------------|
| example.org/logstream | v1.4.0        | v1.4.9      | GHSA-lgst-3f2p-cve-2024-a |
| example.org/httpmux   | v0.5.2        | v0.5.9      | GHSA-hmux-9v4q-cve-2024-b |
| example.org/toolchain | v0.9.0        | v0.9.9      | GHSA-tchn-8x2r-cve-2024-c |

## Required exclude directives (policy invariants)

The following exclude directives must remain declared in the root
`go.mod` at all times. Removing a required exclude is a policy
violation, and no module may resolve to a version that exactly matches
an excluded version. The excluded version is not a starting condition;
it is a permanent invariant that survives every reconciliation.

| Module                | Excluded version |
|-----------------------|------------------|
| example.org/toolchain | v0.9.0           |
| example.org/logstream | v1.4.2           |

## Prohibited replacements

The following module paths may not be replaced anywhere in the
workspace, neither in the root `go.mod` nor in any sub-tree `go.mod`.
Attempts to route around a retract, window, or floor violation via a
replace directive on these paths are rejected even if the replacement
target technically satisfies the floor.

| Module                    |
|---------------------------|
| internal.example/platform |
| example.org/serde         |

## Vendor ledger discipline

Each `## explicit; go X.Y` comment line in the vendor `modules.txt`
must name the same `go` directive value that the effective module
publishes for the resolved version. Ledger comments whose `go X.Y`
value disagrees with the effective module's own `go` directive are
treated as vendor drift alongside the `+incompatible` tag drift and
missing-entry drift already surfaced by the harness.

## Retract interaction

A retract range published by a module's own tip revision is not a
downgrade signal. Selected versions must be simultaneously at or above
the floor, at or below the maximum, and outside every published retract
range. Where a retract range partially overlaps the window, the
effective selection must advance to the **highest non-retracted,
non-excluded** version inside the window.

## Toolchain directive format

Any `toolchain` directive declared in a workspace `go.mod` (root or
sub-tree) must use the bare minor-version format `goX.Y` (for example
`go1.23`). Patch-suffixed forms such as `go1.23.4` and any
`toolchain-` prefix variants are rejected. The matrix profile names
(`go1.22`, `go1.23`) follow the same bare-minor form and are the only
valid values a `toolchain` directive may name.

## Retained fork replacements

The following replace directives are permanent policy invariants. They
must remain declared in both the root `go.mod` and every sub-tree
`go.mod` as an *unversioned* replace (module path alone on the left of
`=>`, no version selector). The fork path must be the listed path and
the fork version must be at or above the minimum fork version (and
still inside the version window for the replaced module). A
version-specific left-hand side does not satisfy this invariant, even
when the right-hand side names the correct fork. Dropping a retained
fork to silence a single matrix cell is a policy violation even when
the upstream path would otherwise resolve cleanly.

| Module              | Fork path                | Min fork version |
|---------------------|--------------------------|------------------|
| example.org/httpmux | example.org/httpmux-fork | v0.5.4           |

## Fork adoption

Where a fork is used as an in-tree replacement, both the root module
and every sub-module in the same repository must agree on the fork
identity. Disagreeing replacement targets are treated as a policy
violation regardless of which version each selects. Fork repositories
that carry backported patches must publish tags that fall inside the
version window to remain valid replacements. When a retained fork's
own module publishes a `go` directive newer than an older matrix
profile, the workspace must still produce a clean cell for that
profile without abandoning the retained fork.
