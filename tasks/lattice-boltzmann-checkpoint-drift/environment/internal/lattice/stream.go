package lattice

// Stream pulls populations from neighbors (ghosts must already be filled).
func Stream(f []float64, nx, ny, g int) {
	tmp := make([]float64, len(f))
	copy(tmp, f)
	for y := g; y < ny+g; y++ {
		for x := g; x < nx+g; x++ {
			for q := 0; q < 9; q++ {
				xs := x - cx[q]
				ys := y - cy[q]
				*at(tmp, x, y, q, nx, ny, g) = *at(f, xs, ys, q, nx, ny, g)
			}
		}
	}
	copy(f, tmp)
}

// ApplyLid biases the top interior row toward a target ux (cavity / couette).
func ApplyLid(f []float64, nx, ny, g int, uLid float64) {
	y := ny + g - 1
	for x := g; x < nx+g; x++ {
		rho, _, _ := Moments(f, x, y, nx, ny, g)
		if rho < 1e-15 {
			rho = 1
		}
		setEq(f, x, y, nx, ny, g, rho, uLid, 0)
	}
}
