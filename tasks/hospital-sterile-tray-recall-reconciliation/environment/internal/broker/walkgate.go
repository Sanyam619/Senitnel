package broker

import "csp.local/reconcile/internal/cfg"

func EnableWalk() bool {
	if cfg.WalkN() {
		return false
	}
	return true
}
