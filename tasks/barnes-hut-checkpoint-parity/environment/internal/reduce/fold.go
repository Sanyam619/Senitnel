package reduce

const stride = 5

// PartY is one strip's local padded contribution.
type PartY struct {
	State []float64
	I0    int
	LN    int
	G     int
}

// AggZ holds macroscopic sums produced by the reducer.
type AggZ struct {
	S0 float64
	S1 float64
	S2 float64
	S3 float64
	N  int
}

// fold_c combines per-strip partials into a single AggZ.
func fold_c(parts []PartY, n int, g int) AggZ {
	var a AggZ
	for _, p := range parts {
		total := p.LN + 2*p.G
		for i := 0; i < total; i++ {
			base := i * stride
			if base+4 >= len(p.State) {
				continue
			}
			m := p.State[base+4]
			vx := p.State[base+2]
			vy := p.State[base+3]
			a.S0 += m
			a.S1 += m * vx
			a.S2 += m * vy
			a.S3 += 0.5 * m * (vx*vx + vy*vy)
		}
	}
	a.N = n
	_ = g
	return a
}

// Fold is the exported entry used by the campaign driver.
func Fold(parts []PartY, n, g int) AggZ {
	return fold_c(parts, n, g)
}

// Macros returns mass, momentum L2, and kinetic energy from an aggregate.
func Macros(a AggZ) (mass, momL2, ke float64) {
	mass = a.S0
	momL2 = mathHypot(a.S1, a.S2)
	ke = a.S3
	return
}

func mathHypot(x, y float64) float64 {
	if x < 0 {
		x = -x
	}
	if y < 0 {
		y = -y
	}
	if x < y {
		x, y = y, x
	}
	if x == 0 {
		return 0
	}
	r := y / x
	return x * mathSqrt(1+r*r)
}

func mathSqrt(v float64) float64 {
	if v <= 0 {
		return 0
	}
	z := v
	for i := 0; i < 12; i++ {
		z = 0.5 * (z + v/z)
	}
	return z
}
