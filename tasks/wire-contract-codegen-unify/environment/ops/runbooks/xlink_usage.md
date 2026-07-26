# xlink usage

`/app/bin/xlink report --out <path>` merges per-lane row dumps from foldctl, sievectl, and the Java main entry, then writes a single JSON document.

Probe subcommands:

- `/app/bin/xlink probe-binary` — encodes and decodes a sample frame across lanes
- `/app/bin/xlink probe-json` — round-trips JSON field names across lanes

Both probes print a small JSON object with a `status` field.
