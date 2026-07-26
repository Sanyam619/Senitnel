package partition

// ExchangeX copies west/east interior edges into neighbor ghost columns (periodic X).
func ExchangeX(f []float64, nx, ny, g int) {
	for y := 0; y < ny+2*g; y++ {
		for q := 0; q < 9; q++ {
			*at(f, g-1, y, q, nx, g) = *at(f, nx+g-1, y, q, nx, g)
			*at(f, nx+g, y, q, nx, g) = *at(f, g, y, q, nx, g)
		}
	}
}

// ExchangeY copies south/north interior edges into neighbor ghost rows (periodic Y).
func ExchangeY(f []float64, nx, ny, g int) {
	stride := nx + 2*g
	for x := 0; x < stride; x++ {
		for q := 0; q < 9; q++ {
			*at(f, x, g-1, q, nx, g) = *at(f, x, ny+g-1, q, nx, g)
			*at(f, x, ny+g, q, nx, g) = *at(f, x, g, q, nx, g)
		}
	}
}

func at(f []float64, x, y, q, nx, g int) *float64 {
	stride := nx + 2*g
	return &f[9*(x+stride*y)+q]
}

// LocalView copies one strip's padded window (including ghosts) from global field.
// Local x=0 maps to global padded coordinate s.X0 (west ghost of the strip).
func LocalView(f []float64, s Strip, nx, ny, g int) []float64 {
	lx := s.X1 - s.X0
	stride := lx + 2*g
	out := make([]float64, 9*stride*(ny+2*g))
	for y := 0; y < ny+2*g; y++ {
		for x := 0; x < lx+2*g; x++ {
			gx := s.X0 + x
			for q := 0; q < 9; q++ {
				out[9*(x+stride*y)+q] = *at(f, gx, y, q, nx, g)
			}
		}
	}
	return out
}
