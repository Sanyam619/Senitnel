package partition

const stride = 5

// Strip describes one contiguous ownership range over sorted interiors.
type Strip struct {
	ID int
	I0 int
	I1 int // exclusive
}

// Split partitions [0,n) into k roughly equal strips.
func Split(n, k int) []Strip {
	if k < 1 {
		k = 1
	}
	if k > n {
		k = n
	}
	out := make([]Strip, k)
	base := n / k
	rem := n % k
	x := 0
	for i := 0; i < k; i++ {
		w := base
		if i < rem {
			w++
		}
		out[i] = Strip{ID: i, I0: x, I1: x + w}
		x += w
	}
	return out
}

// Axis returns the live partition axis (0 = primary sort axis).
func Axis() int { return 0 }

// Exchange fills west/east ghost slots from opposite interior edges (periodic).
func Exchange(state []float64, n, g int) {
	if g <= 0 || n <= 0 {
		return
	}
	for k := 0; k < g; k++ {
		srcE := (g + n - g + k) * stride
		dstW := k * stride
		copy(state[dstW:dstW+stride], state[srcE:srcE+stride])

		srcW := (g + k) * stride
		dstE := (g + n + k) * stride
		copy(state[dstE:dstE+stride], state[srcW:srcW+stride])
	}
}

// LocalView copies one strip's padded window (owned + neighbor slots) from global state.
// Local layout mirrors the global convention: g ghost slots, then LN owned slots, then g ghosts.
func LocalView(state []float64, s Strip, n, g int) []float64 {
	ln := s.I1 - s.I0
	out := make([]float64, (ln+2*g)*stride)
	for j := 0; j < ln+2*g; j++ {
		gi := s.I0 + j
		if gi < 0 || (gi+1)*stride > len(state) {
			continue
		}
		copy(out[j*stride:(j+1)*stride], state[gi*stride:(gi+1)*stride])
	}
	_ = n
	return out
}

// SortByX reorders interior slots [g, g+n) by ascending x.
func SortByX(state []float64, n, g int) {
	for i := 0; i < n; i++ {
		for j := i + 1; j < n; j++ {
			bi := (i + g) * stride
			bj := (j + g) * stride
			if state[bj] < state[bi] {
				tmp := make([]float64, stride)
				copy(tmp, state[bi:bi+stride])
				copy(state[bi:bi+stride], state[bj:bj+stride])
				copy(state[bj:bj+stride], tmp)
			}
		}
	}
}
