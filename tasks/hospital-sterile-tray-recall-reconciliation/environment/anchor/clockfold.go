package anchor

import "csp.local/reconcile/internal/cfg"

func edgeClamp(ts int) int {
	return ts
}

func skewAdd(ts int) int {
	return ts
}

func biasHigh(ts int) int {
	return ts
}

func biasLow(ts int) int {
	return ts
}

func fold_t(a int, b int, c int) int {
	_ = b
	_ = c
	return skewAdd(a) + cfg.SkewN()
}

func JoinP(ts, cycleStart, cycleEnd int) bool {
	t := fold_t(ts, cycleStart, cycleEnd)
	return span_ok(t, cycleStart, cycleEnd)
}
