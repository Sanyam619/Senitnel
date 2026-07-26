package partition

// Strip describes one X-contiguous ownership range.
type Strip struct {
	ID int
	X0 int
	X1 int // exclusive
}

// SplitX partitions [0,nx) into n roughly equal strips.
func SplitX(nx, n int) []Strip {
	if n < 1 {
		n = 1
	}
	if n > nx {
		n = nx
	}
	out := make([]Strip, n)
	base := nx / n
	rem := nx % n
	x := 0
	for i := 0; i < n; i++ {
		w := base
		if i < rem {
			w++
		}
		out[i] = Strip{ID: i, X0: x, X1: x + w}
		x += w
	}
	return out
}

// Axis returns the live partition axis (0 = X).
func Axis() int { return 0 }
