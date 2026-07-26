package stamp

// Prefix returns the first 8 bytes of b (or all of b if shorter).
func Prefix(b []byte) []byte {
	if len(b) <= 8 {
		out := make([]byte, len(b))
		copy(out, b)
		return out
	}
	out := make([]byte, 8)
	copy(out, b[:8])
	return out
}

func Match(a, b []byte) bool {
	pa, pb := Prefix(a), Prefix(b)
	if len(pa) != len(pb) {
		return false
	}
	for i := range pa {
		if pa[i] != pb[i] {
			return false
		}
	}
	return true
}
