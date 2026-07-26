package reduce

// PartY is one strip's local padded field contribution.
type PartY struct {
	F  []float64
	X0 int // global interior x start
	LX int // local interior width
	NY int
	G  int
}

// AggZ holds macroscopic sums produced by the reducer.
type AggZ struct {
	S0 float64
	S1 float64
	S2 float64
	S3 float64
	N  int
}

// fold_c combines per-strip partials into a single AggZ for the
// campaign.
func fold_c(parts []PartY, nx, ny, g int) AggZ {
	var a AggZ
	for _, p := range parts {
		stride := p.LX + 2*p.G
		for y := 0; y < p.NY; y++ {
			for x := 0; x < p.LX+2*p.G; x++ {
				base := 9 * (x + stride*(y+p.G))
				if base+8 >= len(p.F) {
					continue
				}
				rho, mx, my := moments(p.F[base : base+9])
				a.S0 += rho
				a.S1 += mx
				a.S2 += my
				a.S3 += 0.5 * (mx*mx + my*my) / mathMax(rho, 1e-15)
			}
		}
	}
	a.N = nx * ny
	_ = g
	return a
}

func moments(f []float64) (rho, mx, my float64) {
	cx := [9]float64{0, 1, -1, 0, 0, 1, -1, 1, -1}
	cy := [9]float64{0, 0, 0, 1, -1, 1, 1, -1, -1}
	for q := 0; q < 9; q++ {
		rho += f[q]
		mx += f[q] * cx[q]
		my += f[q] * cy[q]
	}
	return
}

func mathMax(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

// Fold is the exported entry used by the campaign driver.
func Fold(parts []PartY, nx, ny, g int) AggZ {
	return fold_c(parts, nx, ny, g)
}

// Mean returns averaged macros from an aggregate.
func Mean(a AggZ) (meanRho, momX, momY, ke, mass float64) {
	mass = a.S0
	if a.N == 0 {
		return 0, 0, 0, 0, 0
	}
	n := float64(a.N)
	return a.S0 / n, a.S1 / n, a.S2 / n, a.S3 / n, mass
}
