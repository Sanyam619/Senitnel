Terms used throughout the rig documentation.

- **boot epoch** — a monotonically increasing integer the server bumps on
  every restart. Delegations issued under one epoch cannot be reclaimed
  under a different one.
- **stateid sequence** — a per-open-owner integer that increments on
  each state-changing operation. Higher-seq records supersede lower-seq
  ones for the same owner.
- **delegation** — a per-client cache authority on a file handle.
  `write` grants exclusive modification rights; `read` grants stability.
- **share reservation** — a weaker access mode a delegation can be
  downgraded into when two clients contend for a write delegation.
- **grace window** — the interval after a server restart during which
  clients may re-establish their pre-reboot state. Records arriving
  after the window closes are silently discarded.
- **server-side COPY** — RFC 7862 offloaded copy: the server reads from
  a source handle and writes to a destination handle, emitting a
  `write_verifier4` when the operation is durable.
- **focused handle** — for an episode, the file handle recorded as the
  COPY source. Every reconciled decision is anchored on this handle.
