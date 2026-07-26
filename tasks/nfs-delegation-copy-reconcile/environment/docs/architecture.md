Site Recovery Layout
====================

Three roles appear in the captured reboot episodes.

- `srv`  — the NFS server side: reclaim journal, namespace, and copy
           intent state at the reboot instant.
- `cliA` — the client that reclaims a write delegation on the focused
           handle and, in some episodes, issues a RENAME.
- `cliB` — the client that issues the server-side COPY and, in some
           episodes, holds a read or write delegation on the source
           handle.

Each episode directory under `data/episodes/` is a frozen on-disk
snapshot from one unclean restart. Recovery reads those journals only —
no live NFS daemons are running in the lab container.
