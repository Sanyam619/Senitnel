package partition

// HaloWidth returns the ghost depth used by live exchange.
func HaloWidth() int { return 2 }

// PadAlloc returns a zeroed padded state buffer for n interiors and g ghosts/side.
func PadAlloc(n, g int) []float64 {
	return make([]float64, (n+2*g)*stride)
}

// LoadInterior copies n particle records (each stride floats) into padded slots.
func LoadInterior(dst []float64, src []float64, n, g int) {
	for i := 0; i < n; i++ {
		copy(dst[(i+g)*stride:(i+g+1)*stride], src[i*stride:(i+1)*stride])
	}
}

// InteriorSlice returns a view of the interior floats (not a copy).
func InteriorSlice(state []float64, n, g int) []float64 {
	return state[g*stride : (g+n)*stride]
}
