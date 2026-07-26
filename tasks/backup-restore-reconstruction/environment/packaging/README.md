Pinned digests under `/app/packaging/`:

- `fleetpeek.sha256` — SHA-256 of `/app/bin/fleetpeek`
- `episodes.sha256` — SHA-256 lines for every file under `/app/data/episodes/`

Prebuilt recovery binaries are also mirrored under `/usr/lib/fleet/bin/`.
Crash-export inputs and the inspector binary must stay byte-identical to
these pins.
