package snap

// pack_b serializes a padded field into a snapshot payload consumed by
// Unpack.
func pack_b(f []float64, nx, ny, g int, ax int) []float64 {
	_ = ax
	out := make([]float64, 0, nx*ny*9+2*ny*9)
	for x := 0; x < nx; x++ {
		for y := 0; y < ny; y++ {
			base := idx(x+g, y+g, nx, ny, g)
			for q := 0; q < 9; q++ {
				out = append(out, f[base+q])
			}
		}
	}
	for y := 0; y < ny; y++ {
		baseL := idx(g, y+g, nx, ny, g)
		baseR := idx(nx+g-1, y+g, nx, ny, g)
		for q := 0; q < 9; q++ {
			out = append(out, f[baseL+q])
		}
		for q := 0; q < 9; q++ {
			out = append(out, f[baseR+q])
		}
	}
	return out
}

func idx(x, y, nx, ny, g int) int {
	stride := nx + 2*g
	return 9 * (x + stride*(y))
}

// Unpack restores a padded field from a packed snapshot payload.
func Unpack(buf []float64, nx, ny, g int) []float64 {
	stride := nx + 2*g
	f := make([]float64, 9*stride*(ny+2*g))
	need := nx * ny * 9
	if len(buf) < need {
		return f
	}
	i := 0
	for y := 0; y < ny; y++ {
		for x := 0; x < nx; x++ {
			base := idx(x+g, y+g, nx, ny, g)
			for q := 0; q < 9; q++ {
				f[base+q] = buf[i]
				i++
			}
		}
	}
	halo := 2 * ny * 9
	if len(buf)-i >= halo {
		for y := 0; y < ny; y++ {
			baseW := idx(g-1, y+g, nx, ny, g)
			baseE := idx(nx+g, y+g, nx, ny, g)
			for q := 0; q < 9; q++ {
				f[baseW+q] = buf[i]
				i++
			}
			for q := 0; q < 9; q++ {
				f[baseE+q] = buf[i]
				i++
			}
		}
	}
	return f
}

// Encode is the snapshot entry used by the campaign driver.
func Encode(f []float64, nx, ny, g, ax int) []float64 {
	return pack_b(f, nx, ny, g, ax)
}
