package tree

/*
#cgo CFLAGS: -O2 -I${SRCDIR}/../../native
#cgo LDFLAGS: -lm
#include "force.h"
*/
import "C"

const stride = 5

// PairForce returns softened force on body 0 due to body 1 (G absorbed by caller).
func PairForce(x0, y0, x1, y1, m1, soft float64) (fx, fy float64) {
	var cfx, cfy C.double
	C.nb_pair_force(
		C.double(x0), C.double(y0), C.double(x1), C.double(y1),
		C.double(m1), C.double(soft), &cfx, &cfy,
	)
	return float64(cfx), float64(cfy)
}

// MonoForce returns softened force on (x0,y0) from a monopole.
func MonoForce(x0, y0, cx, cy, m, soft float64) (fx, fy float64) {
	var cfx, cfy C.double
	C.nb_mono_force(
		C.double(x0), C.double(y0), C.double(cx), C.double(cy),
		C.double(m), C.double(soft), &cfx, &cfy,
	)
	return float64(cfx), float64(cfy)
}
