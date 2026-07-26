Recorded episodes live in `episodes/` after the image builds. Each
subdirectory holds one crash story:

- server_reclaim.log — the server's reclaim journal
- client_a_ops.log   — client A's operation stream (delegation holder)
- client_b_ops.log   — client B's operation stream (COPY issuer)
- copy_intent.rec    — the server-side COPY intent record
- namespace.snap     — the on-disk namespace snapshot post-reboot

episode_manifest.json lists the focused (COPY source) file handle for
each episode as a 32-char hex string.
