#!/bin/bash
set -euo pipefail

cd /app

# --- Location A: manifest blob wins over build-meta ---
python3 - <<'PY'
import re
from pathlib import Path

path = Path("internal/policy/pick.go")
src = path.read_text()
pattern = re.compile(
    r"(func op_a\(m blobX, b blobX\) blobX \{\s*"
    r"if m\.U != b\.U \|\| m\.V != b\.V \|\| m\.P != b\.P \{\s*"
    r"return )b(\s*\}\s*"
    r"return m\s*\})",
    re.MULTILINE,
)
new_src, count = pattern.subn(r"\1m\2", src)
if count != 1:
    raise SystemExit(f"expected exactly one op_a match, got {count}")
path.write_text(new_src)
PY

# --- Location B: slot-order body + primary-axis halo appendix ---
python3 - <<'PY'
from pathlib import Path

Path("internal/snap/encode.go").write_text("""package snap

const stride = 5 // x,y,vx,vy,m per slot

// pack_b serializes a padded state into a snapshot payload consumed by
// Unpack.
func pack_b(state []float64, n int, g int, ax int) []float64 {
	out := make([]float64, 0, (n+2*g)*stride)
	for i := 0; i < n; i++ {
		base := (i + g) * stride
		out = append(out, state[base:base+stride]...)
	}
	if ax == 0 {
		for i := 0; i < g; i++ {
			base := (g + i) * stride
			out = append(out, state[base:base+stride]...)
		}
		for i := 0; i < g; i++ {
			base := (g + n - g + i) * stride
			out = append(out, state[base:base+stride]...)
		}
	} else {
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
		for i := 0; i < g && i < len(ranked); i++ {
			base := ranked[i].idx * stride
			out = append(out, state[base:base+stride]...)
		}
		for i := 0; i < g && i < len(ranked); i++ {
			base := ranked[len(ranked)-1-i].idx * stride
			out = append(out, state[base:base+stride]...)
		}
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
""")
PY

# --- Location C: interior-range reduction ---
python3 - <<'PY'
from pathlib import Path

Path("internal/reduce/fold.go").write_text("""package reduce

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
		for i := p.G; i < p.G+p.LN; i++ {
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
			a.N++
		}
	}
	_ = n
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
""")
PY

CGO_ENABLED=1 go build -trimpath -o /app/bin/campaign ./cmd/campaign
mkdir -p /output
/app/scripts/run_campaign.sh /output/campaign-report.json
