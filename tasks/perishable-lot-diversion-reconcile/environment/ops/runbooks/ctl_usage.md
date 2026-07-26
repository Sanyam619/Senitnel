# ctl operator reference

`/app/bin/ctl` reads shipment ledgers from `/app/data` and operator tables from `/app/config/l7`.

Read-only probes: `status`, `query point`, `query scan`.

State-changing operations: `bind`, `sweep`, `seal --lane <lane>`, `report --out PATH`.

Point lookups resolve against live runtime and route ledgers. Range scans resolve against the sealed sidecar for that lane.

After editing `/app/src`, rebuild with `rustc --edition=2021 main.rs -O -o /app/bin/ctl` from `/app/src`.
