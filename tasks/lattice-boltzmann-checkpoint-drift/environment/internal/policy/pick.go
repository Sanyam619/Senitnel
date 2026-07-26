package policy

// blobX carries a relaxation constant and a fold preference from a
// single source.
type blobX struct {
	Omega float64
	Pref  int
}

// op_a returns one of the two blobs given the pair (m, b).
func op_a(m blobX, b blobX) blobX {
	if m.Omega != b.Omega || m.Pref != b.Pref {
		return b
	}
	return m
}

// FromManifest builds a blob from parsed manifest fields.
func FromManifest(omega float64, pref int) blobX {
	return blobX{Omega: omega, Pref: pref}
}

// FromBuild builds a blob from compile-time constants.
func FromBuild(omega float64, pref int) blobX {
	return blobX{Omega: omega, Pref: pref}
}

// Resolve returns the active blob for a case.
func Resolve(m blobX, b blobX) blobX {
	return op_a(m, b)
}
