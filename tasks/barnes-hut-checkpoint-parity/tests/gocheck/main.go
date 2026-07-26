// Package main is the verifier-owned behavioral checker for the N-body
// campaign. It is not part of the agent-facing surface: /tests/conftest.py
// copies this file under /app/cmd/nbverify/ on every verifier invocation
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

	"nbody.campaign/runner/internal/partition"
	"nbody.campaign/runner/internal/policy"
	"nbody.campaign/runner/internal/reduce"
	"nbody.campaign/runner/internal/snap"
)

const stride = 5

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(1)
}

func approx(a, b float64) bool {
	d := math.Abs(a - b)
	scale := math.Max(math.Max(math.Abs(a), math.Abs(b)), 1.0)
	return d/scale < 1e-9
}

func checkPolicy() {
	manU, manV, manP := 0.42, 0.11, 0
	buildU, buildV, buildP := 1.77, 0.88, 1
	m := policy.FromX(manU, manV, manP)
	b := policy.FromY(buildU, buildV, buildP)
	r := policy.Sel(m, b)
	if r.U != manU || r.V != manV || r.P != manP {
		fail("policy.Sel did not honor the sheet blob: got u=%v v=%v p=%d, want u=%v v=%v p=%d",
			r.U, r.V, r.P, manU, manV, manP)
	}
	swap := policy.Sel(policy.FromX(0.61, 0.07, 1), policy.FromY(1.2, 0.4, 0))
	if swap.U != 0.61 || swap.V != 0.07 || swap.P != 1 {
		fail("policy.Sel failed on swapped inputs: got u=%v v=%v p=%d", swap.U, swap.V, swap.P)
	}
	same := policy.Sel(m, m)
	if same.U != manU || same.V != manV || same.P != manP {
		fail("policy.Sel identity failed: got u=%v v=%v p=%d", same.U, same.V, same.P)
	}
}

func checkSnapRoundTrip() {
	n, g := 12, 2
	state := make([]float64, (n+2*g)*stride)
	for i := 0; i < n+2*g; i++ {
		base := i * stride
		state[base+0] = float64(i) + 0.1
		state[base+1] = float64(100-i) + 0.2
		state[base+2] = float64(i) * 0.01
		state[base+3] = float64(-i) * 0.01
		state[base+4] = 1.0 / float64(n)
	}

	packed := snap.Encode(state, n, g, partition.Axis())
	wantLen := (n + 2*g) * stride
	if len(packed) != wantLen {
		fail("snap.Encode payload length: got %d, want %d (interior+halo)",
			len(packed), wantLen)
	}

	state2 := snap.Unpack(packed, n, g)

	for i := 0; i < n; i++ {
		base := (i + g) * stride
		for q := 0; q < stride; q++ {
			if state[base+q] != state2[base+q] {
				fail("snap round-trip interior mismatch at i=%d q=%d: got %v, want %v",
					i, q, state2[base+q], state[base+q])
			}
		}
	}

	for k := 0; k < g; k++ {
		srcW := (g + k) * stride
		dstW := k * stride
		srcE := (g + n - g + k) * stride
		dstE := (g + n + k) * stride
		for q := 0; q < stride; q++ {
			if state2[dstW+q] != state[srcW+q] {
				fail("snap west ghost mismatch at k=%d q=%d: got %v, want %v",
					k, q, state2[dstW+q], state[srcW+q])
			}
			if state2[dstE+q] != state[srcE+q] {
				fail("snap east ghost mismatch at k=%d q=%d: got %v, want %v",
					k, q, state2[dstE+q], state[srcE+q])
			}
		}
	}
}

func foldWith(state []float64, n, g, workers int) reduce.AggZ {
	strips := partition.Split(n, workers)
	parts := make([]reduce.PartY, 0, len(strips))
	for _, s := range strips {
		view := partition.LocalView(state, s, n, g)
		parts = append(parts, reduce.PartY{
			State: view, I0: s.I0, LN: s.I1 - s.I0, G: g,
		})
	}
	return reduce.Fold(parts, n, g)
}

func checkReduceIndependent() {
	n, g := 16, 2
	state := make([]float64, (n+2*g)*stride)
	for i := 0; i < n+2*g; i++ {
		base := i * stride
		state[base+0] = float64(i)
		state[base+1] = float64(i) * 0.5
		state[base+2] = 0.01 * float64(i)
		state[base+3] = -0.02 * float64(i)
		state[base+4] = 0.25 + 0.01*float64(i)
	}

	var refS0, refS1, refS2 float64
	for i := 0; i < n; i++ {
		base := (i + g) * stride
		m := state[base+4]
		refS0 += m
		refS1 += m * state[base+2]
		refS2 += m * state[base+3]
	}

	a1 := foldWith(state, n, g, 1)
	a2 := foldWith(state, n, g, 2)
	a4 := foldWith(state, n, g, 4)

	if !approx(a1.S0, a2.S0) || !approx(a1.S0, a4.S0) {
		fail("reduce.Fold mass diverges across workers: w1=%v w2=%v w4=%v",
			a1.S0, a2.S0, a4.S0)
	}
	if !approx(a1.S1, a2.S1) || !approx(a1.S1, a4.S1) {
		fail("reduce.Fold px diverges across workers: w1=%v w2=%v w4=%v",
			a1.S1, a2.S1, a4.S1)
	}
	if !approx(a1.S2, a2.S2) || !approx(a1.S2, a4.S2) {
		fail("reduce.Fold py diverges across workers: w1=%v w2=%v w4=%v",
			a1.S2, a2.S2, a4.S2)
	}
	if a1.N != a2.N || a1.N != a4.N {
		fail("reduce.Fold N diverges across workers: w1=%d w2=%d w4=%d",
			a1.N, a2.N, a4.N)
	}
	if !approx(a1.S0, refS0) {
		fail("reduce.Fold mass includes non-interior contributions: got %v, want %v",
			a1.S0, refS0)
	}
	if !approx(a1.S1, refS1) {
		fail("reduce.Fold px includes non-interior contributions: got %v, want %v",
			a1.S1, refS1)
	}
	if !approx(a1.S2, refS2) {
		fail("reduce.Fold py includes non-interior contributions: got %v, want %v",
			a1.S2, refS2)
	}
	if a1.N != n {
		fail("reduce.Fold N mismatch: got %d, want %d", a1.N, n)
	}
}

func main() {
	if len(os.Args) < 2 {
		fail("usage: nbverify <policy|snap|reduce|all>")
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
