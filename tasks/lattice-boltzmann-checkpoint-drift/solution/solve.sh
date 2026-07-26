#!/bin/bash
set -euo pipefail

cd /app

# --- Location A: manifest blob wins over build-meta ---
# Surgical: flip the disagreement branch in op_a from `return b` to `return m`.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("internal/policy/pick.go")
src = path.read_text()
pattern = re.compile(
    r"(func op_a\(m blobX, b blobX\) blobX \{\s*"
    r"if m\.Omega != b\.Omega \|\| m\.Pref != b\.Pref \{\s*"
    r"return )b(\s*\}\s*"
    r"return m\s*\})",
    re.MULTILINE,
)
new_src, count = pattern.subn(r"\1m\2", src)
if count != 1:
    raise SystemExit(f"expected exactly one op_a match, got {count}")
path.write_text(new_src)
PY

# --- Location B: row-major interior + X-edge halo matching live exchange ---
cat > internal/snap/encode.go <<'EOF'
package snap

// pack_b flattens the field into a snapshot payload: an interior body
// followed by a halo appendix. ax selects the halo axis convention:
// ax==0 emits west/east edge pairs (live X partition); otherwise
// south/north pairs.
func pack_b(f []float64, nx, ny, g int, ax int) []float64 {
	out := make([]float64, 0, nx*ny*9+2*ny*9)
	for y := 0; y < ny; y++ {
		for x := 0; x < nx; x++ {
			base := idx(x+g, y+g, nx, ny, g)
			for q := 0; q < 9; q++ {
				out = append(out, f[base+q])
			}
		}
	}
	if ax == 0 {
		for y := 0; y < ny; y++ {
			baseW := idx(g, y+g, nx, ny, g)
			baseE := idx(nx+g-1, y+g, nx, ny, g)
			for q := 0; q < 9; q++ {
				out = append(out, f[baseW+q])
			}
			for q := 0; q < 9; q++ {
				out = append(out, f[baseE+q])
			}
		}
	} else {
		for x := 0; x < nx; x++ {
			baseS := idx(x+g, g, nx, ny, g)
			baseN := idx(x+g, ny+g-1, nx, ny, g)
			for q := 0; q < 9; q++ {
				out = append(out, f[baseS+q])
			}
			for q := 0; q < 9; q++ {
				out = append(out, f[baseN+q])
			}
		}
	}
	return out
}

func idx(x, y, nx, ny, g int) int {
	stride := nx + 2*g
	return 9 * (x + stride*(y))
}

// Unpack loads a packed slice into a padded field. The interior is
// populated in row-major order; a trailing halo appendix, when present,
// is unpacked into the X ghost columns so the restored field matches the
// partition exchange layout used by the campaign driver.
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
EOF

# --- Location C: interior-only fold, denominator = cells contributing ---
cat > internal/reduce/fold.go <<'EOF'
package reduce

// PartY is one strip's local padded field contribution.
type PartY struct {
	F  []float64
	X0 int
	LX int
	NY int
	G  int
}

// AggZ holds macroscopic sums over interior cells.
type AggZ struct {
	S0 float64
	S1 float64
	S2 float64
	S3 float64
	N  int
}

// fold_c reduces per-strip partials into a single AggZ.
// Only interior cells contribute; each cell is accumulated exactly once
// and N tracks the actual count of contributing cells.
func fold_c(parts []PartY, nx, ny, g int) AggZ {
	var a AggZ
	for _, p := range parts {
		stride := p.LX + 2*p.G
		for y := 0; y < p.NY; y++ {
			for x := p.G; x < p.G+p.LX; x++ {
				base := 9 * (x + stride*(y+p.G))
				if base+8 >= len(p.F) {
					continue
				}
				rho, mx, my := moments(p.F[base : base+9])
				a.S0 += rho
				a.S1 += mx
				a.S2 += my
				a.S3 += 0.5 * (mx*mx + my*my) / mathMax(rho, 1e-15)
				a.N++
			}
		}
	}
	_ = nx
	_ = ny
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
EOF

go build -trimpath -o /app/bin/campaign ./cmd/campaign
mkdir -p /output
/app/scripts/run_campaign.sh /output/campaign-report.json
