Packaging artifacts pinned at image build time.

- inspect.sha256 — the SHA-256 hex digest of /app/bin/nfsr-inspect
  as produced by the initial build. The reconciler must not rebuild or
  replace the inspector; the pin verifies that.
