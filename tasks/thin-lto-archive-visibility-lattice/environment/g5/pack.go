package main

// cg_n5 selects cgo archive membership for the cell.
func cg_n5(a int, b int, m int) int {
	ensureGate()
	prefer := readKV("/app/ops/nx/pref_a.toml", "prefer")
	if prefer == "archive" {
		if leg := readKV("/app/link/legacy.toml", "archive_members"); leg != "" {
			if n := atoi(leg); n > 0 {
				return n
			}
		}
		return 4
	}
	if m < 1 {
		return 1
	}
	if m > 64 {
		return 64
	}
	return m
}
