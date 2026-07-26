// Package main is the verifier-owned behavioral checker for the LBM
// campaign. It is not part of the agent-facing surface: /tests/conftest.py
// copies this file under /app/cmd/lbmverify/ on every verifier invocation
// so it links against the current internal packages, then builds and runs
// it as an out-of-band binary. It exercises the internal packages with
// inputs the verifier controls, so a fabricated /output/campaign-report.json
// or a doctored /app/scripts/run_campaign.sh cannot mask defects in the
// packages the agent is expected to repair.
package main

import (
	"fmt"
	"math"
	"os"

	"lbm.campaign/runner/internal/partition"
	"lbm.campaign/runner/internal/policy"
	"lbm.campaign/runner/internal/reduce"
	"lbm.campaign/runner/internal/snap"
)

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(1)
}

func approx(a, b float64) bool {
	d := math.Abs(a - b)
	scale := math.Max(math.Max(math.Abs(a), math.Abs(b)), 1.0)
	return d/scale < 1e-9
}

// checkPolicy asserts that policy.Resolve honors the manifest-derived blob
// when the manifest and build-derived blobs disagree, using values the
// verifier picks (not values baked into any package under /app).
func checkPolicy() {
	manOmega, manPref := 0.73, 0
	buildOmega, buildPref := 1.51, 1
	m := policy.FromManifest(manOmega, manPref)
	b := policy.FromBuild(buildOmega, buildPref)
	r := policy.Resolve(m, b)
	if r.Omega != manOmega || r.Pref != manPref {
		fail("policy.Resolve did not honor the manifest blob: got omega=%v pref=%d, want omega=%v pref=%d",
			r.Omega, r.Pref, manOmega, manPref)
	}
	// Second orientation: the opposite pair should not swing the answer.
	swap := policy.Resolve(policy.FromManifest(0.9, 1), policy.FromBuild(1.4, 0))
	if swap.Omega != 0.9 || swap.Pref != 1 {
		fail("policy.Resolve failed on swapped inputs: got omega=%v pref=%d, want omega=0.9 pref=1",
			swap.Omega, swap.Pref)
	}
	// Identity: matching blobs return the shared value.
	same := policy.Resolve(m, m)
	if same.Omega != manOmega || same.Pref != manPref {
		fail("policy.Resolve identity failed: got omega=%v pref=%d", same.Omega, same.Pref)
	}
}

// checkSnapRoundTrip asserts that snap.Encode and snap.Unpack round-trip a
// padded field: the interior is restored in the same slots and the halo
// appendix populates the X ghost columns to match the live partition
// exchange layout.
func checkSnapRoundTrip() {
	nx, ny, g := 8, 6, 1
	stride := nx + 2*g
	f := make([]float64, 9*stride*(ny+2*g))
	// Populate every padded cell so ghost inclusion or a wrong axis choice
	// during Encode will scramble the round-trip.
	for y := 0; y < ny+2*g; y++ {
		for x := 0; x < nx+2*g; x++ {
			base := 9 * (x + stride*y)
			for q := 0; q < 9; q++ {
				f[base+q] = float64(1000*(y+1)+10*(x+1)+q) + 0.25
			}
		}
	}

	packed := snap.Encode(f, nx, ny, g, partition.Axis())
	wantLen := nx*ny*9 + 2*ny*9
	if len(packed) != wantLen {
		fail("snap.Encode payload length: got %d, want %d (interior+X halo)",
			len(packed), wantLen)
	}

	f2 := snap.Unpack(packed, nx, ny, g)

	// Interior cells must round-trip exactly.
	for y := 0; y < ny; y++ {
		for x := 0; x < nx; x++ {
			base := 9 * ((x + g) + stride*(y+g))
			for q := 0; q < 9; q++ {
				if f[base+q] != f2[base+q] {
					fail("snap round-trip interior mismatch at x=%d y=%d q=%d: got %v, want %v",
						x, y, q, f2[base+q], f[base+q])
				}
			}
		}
	}

	// The halo appendix must land in the X ghost columns as the west/east
	// interior edge values.
	for y := 0; y < ny; y++ {
		interiorW := 9 * (g + stride*(y+g))
		interiorE := 9 * (nx + g - 1 + stride*(y+g))
		ghostW := 9 * ((g - 1) + stride*(y+g))
		ghostE := 9 * ((nx + g) + stride*(y+g))
		for q := 0; q < 9; q++ {
			if f2[ghostW+q] != f[interiorW+q] {
				fail("snap west ghost mismatch at y=%d q=%d: got %v, want %v (interior west edge)",
					y, q, f2[ghostW+q], f[interiorW+q])
			}
			if f2[ghostE+q] != f[interiorE+q] {
				fail("snap east ghost mismatch at y=%d q=%d: got %v, want %v (interior east edge)",
					y, q, f2[ghostE+q], f[interiorE+q])
			}
		}
	}
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

func foldWith(f []float64, nx, ny, g, workers int) reduce.AggZ {
	strips := partition.SplitX(nx, workers)
	parts := make([]reduce.PartY, 0, len(strips))
	for _, s := range strips {
		view := partition.LocalView(f, s, nx, ny, g)
		parts = append(parts, reduce.PartY{
			F: view, X0: s.X0, LX: s.X1 - s.X0, NY: ny, G: g,
		})
	}
	return reduce.Fold(parts, nx, ny, g)
}

// checkReduceIndependent asserts that reduce.Fold reduces only interior
// cells and produces identical aggregates for worker counts 1, 2, and 4
// on a verifier-constructed padded field.
func checkReduceIndependent() {
	nx, ny, g := 8, 4, 1
	stride := nx + 2*g
	f := make([]float64, 9*stride*(ny+2*g))
	// Fill every padded cell (interior + ghost slots) with distinct values
	// so any inclusion of non-interior cells will inflate the aggregate.
	for y := 0; y < ny+2*g; y++ {
		for x := 0; x < nx+2*g; x++ {
			base := 9 * (x + stride*y)
			for q := 0; q < 9; q++ {
				f[base+q] = float64(1000*(y+1)+10*(x+1)+q) + 0.5
			}
		}
	}

	// Independent interior-only reference.
	var refS0, refS1, refS2 float64
	for y := 0; y < ny; y++ {
		for x := 0; x < nx; x++ {
			base := 9 * ((x + g) + stride*(y+g))
			rho, mx, my := moments(f[base : base+9])
			refS0 += rho
			refS1 += mx
			refS2 += my
		}
	}

	a1 := foldWith(f, nx, ny, g, 1)
	a2 := foldWith(f, nx, ny, g, 2)
	a4 := foldWith(f, nx, ny, g, 4)

	if !approx(a1.S0, a2.S0) || !approx(a1.S0, a4.S0) {
		fail("reduce.Fold mass diverges across workers: w1=%v w2=%v w4=%v",
			a1.S0, a2.S0, a4.S0)
	}
	if !approx(a1.S1, a2.S1) || !approx(a1.S1, a4.S1) {
		fail("reduce.Fold x-momentum diverges across workers: w1=%v w2=%v w4=%v",
			a1.S1, a2.S1, a4.S1)
	}
	if !approx(a1.S2, a2.S2) || !approx(a1.S2, a4.S2) {
		fail("reduce.Fold y-momentum diverges across workers: w1=%v w2=%v w4=%v",
			a1.S2, a2.S2, a4.S2)
	}
	if a1.N != a2.N || a1.N != a4.N {
		fail("reduce.Fold N diverges across workers: w1=%d w2=%d w4=%d",
			a1.N, a2.N, a4.N)
	}
	if !approx(a1.S0, refS0) {
		fail("reduce.Fold mass includes non-interior contributions: got %v, want %v (interior-only)",
			a1.S0, refS0)
	}
	if !approx(a1.S1, refS1) {
		fail("reduce.Fold x-momentum includes non-interior contributions: got %v, want %v (interior-only)",
			a1.S1, refS1)
	}
	if !approx(a1.S2, refS2) {
		fail("reduce.Fold y-momentum includes non-interior contributions: got %v, want %v (interior-only)",
			a1.S2, refS2)
	}
	if a1.N != nx*ny {
		fail("reduce.Fold N mismatch: got %d, want %d (interior cell count)",
			a1.N, nx*ny)
	}
}

func main() {
	if len(os.Args) < 2 {
		fail("usage: lbmverify <policy|snap|reduce|all>")
	}
	switch os.Args[1] {
	case "policy":
		checkPolicy()
	case "snap":
		checkSnapRoundTrip()
	case "reduce":
		checkReduceIndependent()
	case "all":
		checkPolicy()
		checkSnapRoundTrip()
		checkReduceIndependent()
	default:
		fail("unknown subcommand: %s", os.Args[1])
	}
	fmt.Println("OK")
}
