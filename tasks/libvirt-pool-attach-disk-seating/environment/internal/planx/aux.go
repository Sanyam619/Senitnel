package planx

// DistinctPools returns the pool names referenced by the roster in first-seen
// order. Used by tooling that needs a stable pool iteration order.
func DistinctPools(rows []Row) []string {
	seen := map[string]bool{}
	var out []string
	for _, r := range rows {
		if !seen[r.Pool] {
			seen[r.Pool] = true
			out = append(out, r.Pool)
		}
	}
	return out
}
