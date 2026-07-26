package policy

// blobX carries an opening knob, a softening knob, and a fold preference
// from a single source.
type blobX struct {
	U float64
	V float64
	P int
}

// op_a returns one of the two blobs given the pair (m, b).
func op_a(m blobX, b blobX) blobX {
	if m.U != b.U || m.V != b.V || m.P != b.P {
		return b
	}
	return m
}

// FromX builds a blob from parsed sheet fields.
func FromX(u, v float64, p int) blobX {
	return blobX{U: u, V: v, P: p}
}

// FromY builds a blob from compile-time constants.
func FromY(u, v float64, p int) blobX {
	return blobX{U: u, V: v, P: p}
}

// Sel returns the active blob for a case.
func Sel(m blobX, b blobX) blobX {
	return op_a(m, b)
}
