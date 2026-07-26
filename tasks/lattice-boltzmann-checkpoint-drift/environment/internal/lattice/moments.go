package lattice

import "math"

// MacroInterior computes mean macros over interior cells (single-rank helper).
func MacroInterior(f []float64, nx, ny, g int) (meanRho, momX, momY, ke, mass float64, stable bool) {
	stable = true
	var n float64
	for y := g; y < ny+g; y++ {
		for x := g; x < nx+g; x++ {
			rho, ux, uy := Moments(f, x, y, nx, ny, g)
			if math.IsNaN(rho) || math.IsInf(rho, 0) {
				stable = false
			}
			mx := rho * ux
			my := rho * uy
			mass += rho
			meanRho += rho
			momX += mx
			momY += my
			ke += 0.5 * (mx*mx + my*my) / math.Max(rho, 1e-15)
			n++
		}
	}
	if n > 0 {
		meanRho /= n
		momX /= n
		momY /= n
		ke /= n
	}
	return
}
