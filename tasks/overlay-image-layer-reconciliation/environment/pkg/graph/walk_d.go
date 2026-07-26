package graph

import "github.com/opencontainers/go-digest"

// WalkD performs a depth-first walk over adjacency rows (telemetry only).
func WalkD(adj map[digest.Digest][]digest.Digest, start digest.Digest) []digest.Digest {
	seen := map[digest.Digest]struct{}{}
	var out []digest.Digest
	var visit func(d digest.Digest)
	visit = func(d digest.Digest) {
		if _, ok := seen[d]; ok {
			return
		}
		seen[d] = struct{}{}
		out = append(out, d)
		for _, n := range adj[d] {
			visit(n)
		}
	}
	visit(start)
	return out
}
