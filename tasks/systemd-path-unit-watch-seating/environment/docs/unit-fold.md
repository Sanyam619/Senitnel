Path unit fold
==============

A path unit's effective watch conditions come from folding the base unit
`/etc/systemd/system/<unit>.path` first, then every drop-in under
`/etc/systemd/system/<unit>.path.d/*.conf` in lexical filename order. Only keys
in the `[Path]` section enter the watch table:

- `PathExists=<path>`
- `PathChanged=<path>`
- `DirectoryNotEmpty=<path>`

Later assignments override earlier ones for the same key across the base and all
drop-ins. An empty value clears that key. Keys in other sections (`[Unit]`,
`[Install]`) do not affect the watch table.

A unit is armed only when its folded `PathExists` and folded `PathChanged` both
match the authoritative durable tip for that unit, its tip and watch generation
are at or above the floor, and it declares no `DirectoryNotEmpty` watch. The
folded `PathExists` and `PathChanged` are what appear in the report regardless of
whether the unit ends armed.

Effective watched paths are strings after the fold. Empty PathExists,
PathChanged, or DirectoryNotEmpty cells are recorded as `-` in the derived
live fold/tip tables so column alignment stays stable. A drop-in named
`90-local.conf` is the operations-managed slot governed by the abort/cutover
receipt (see operator notes); earlier drop-ins carry the durable watch target.
