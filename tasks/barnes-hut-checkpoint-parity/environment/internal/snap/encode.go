package snap

const stride = 5 // x,y,vx,vy,m per slot

// pack_b serializes a padded state into a snapshot payload consumed by
// Unpack.
func pack_b(state []float64, n int, g int, ax int) []float64 {
	_ = ax
	out := make([]float64, 0, (n+2*g)*stride)
	type pair struct {
		idx int
		y   float64
	}
	ranked := make([]pair, 0, n)
	for i := 0; i < n; i++ {
		base := (i + g) * stride
		ranked = append(ranked, pair{idx: i + g, y: state[base+1]})
	}
	for i := 0; i < len(ranked); i++ {
		for j := i + 1; j < len(ranked); j++ {
			if ranked[j].y < ranked[i].y {
				ranked[i], ranked[j] = ranked[j], ranked[i]
			}
		}
	}
	for _, p := range ranked {
		base := p.idx * stride
		out = append(out, state[base:base+stride]...)
	}
	for i := 0; i < g && i < len(ranked); i++ {
		base := ranked[i].idx * stride
		out = append(out, state[base:base+stride]...)
	}
	for i := 0; i < g && i < len(ranked); i++ {
		base := ranked[len(ranked)-1-i].idx * stride
		out = append(out, state[base:base+stride]...)
	}
	return out
}

// Unpack restores a padded state from a packed snapshot payload.
func Unpack(buf []float64, n, g int) []float64 {
	state := make([]float64, (n+2*g)*stride)
	need := n * stride
	if len(buf) < need {
		return state
	}
	i := 0
	for k := 0; k < n; k++ {
		base := (k + g) * stride
		copy(state[base:base+stride], buf[i:i+stride])
		i += stride
	}
	halo := 2 * g * stride
	if len(buf)-i >= halo {
		for k := 0; k < g; k++ {
			base := k * stride
			copy(state[base:base+stride], buf[i:i+stride])
			i += stride
		}
		for k := 0; k < g; k++ {
			base := (g + n + k) * stride
			copy(state[base:base+stride], buf[i:i+stride])
			i += stride
		}
	}
	return state
}

// Encode is the snapshot entry used by the campaign driver.
func Encode(state []float64, n, g, ax int) []float64 {
	return pack_b(state, n, g, ax)
}
