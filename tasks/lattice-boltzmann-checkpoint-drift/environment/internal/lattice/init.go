package lattice

var (
	cx = [9]int{0, 1, -1, 0, 0, 1, -1, 1, -1}
	cy = [9]int{0, 0, 0, 1, -1, 1, 1, -1, -1}
	w  = [9]float64{4.0 / 9.0, 1.0 / 9.0, 1.0 / 9.0, 1.0 / 9.0, 1.0 / 9.0, 1.0 / 36.0, 1.0 / 36.0, 1.0 / 36.0, 1.0 / 36.0}
)

// Alloc returns a zeroed padded field.
func Alloc(nx, ny, g int) []float64 {
	stride := nx + 2*g
	return make([]float64, 9*stride*(ny+2*g))
}

func at(f []float64, x, y, q, nx, ny, g int) *float64 {
	stride := nx + 2*g
	return &f[9*(x+stride*y)+q]
}

// InitEquilibrium fills the full padded domain with equilibrium at (rho0, ux, uy).
func InitEquilibrium(f []float64, nx, ny, g int, rho0, ux, uy float64) {
	for y := 0; y < ny+2*g; y++ {
		for x := 0; x < nx+2*g; x++ {
			setEq(f, x, y, nx, ny, g, rho0, ux, uy)
		}
	}
}

func setEq(f []float64, x, y, nx, ny, g int, rho, ux, uy float64) {
	usq := ux*ux + uy*uy
	for q := 0; q < 9; q++ {
		cu := float64(cx[q])*ux + float64(cy[q])*uy
		*at(f, x, y, q, nx, ny, g) = w[q] * rho * (1 + 3*cu + 4.5*cu*cu - 1.5*usq)
	}
}

// CollideBGK performs in-place BGK collision on interior cells with body force.
func CollideBGK(f []float64, nx, ny, g int, omega, fx, fy float64) {
	for y := g; y < ny+g; y++ {
		for x := g; x < nx+g; x++ {
			rho, ux, uy := Moments(f, x, y, nx, ny, g)
			if rho > 1e-15 {
				ux += 0.5 * fx / rho
				uy += 0.5 * fy / rho
			}
			usq := ux*ux + uy*uy
			for q := 0; q < 9; q++ {
				cu := float64(cx[q])*ux + float64(cy[q])*uy
				feq := w[q] * rho * (1 + 3*cu + 4.5*cu*cu - 1.5*usq)
				fi := at(f, x, y, q, nx, ny, g)
				force := (1 - 0.5*omega) * w[q] * 3 * (float64(cx[q])*fx + float64(cy[q])*fy)
				*fi = *fi + omega*(feq-*fi) + force
			}
		}
	}
}

// Moments returns density and velocity at a padded coordinate.
func Moments(f []float64, x, y, nx, ny, g int) (rho, ux, uy float64) {
	var mx, my float64
	for q := 0; q < 9; q++ {
		v := *at(f, x, y, q, nx, ny, g)
		rho += v
		mx += v * float64(cx[q])
		my += v * float64(cy[q])
	}
	if rho > 1e-15 {
		ux = mx / rho
		uy = my / rho
	}
	return rho, ux, uy
}

// CopyInterior returns a deep copy of the padded field.
func CopyInterior(f []float64) []float64 {
	out := make([]float64, len(f))
	copy(out, f)
	return out
}
