package decoy

func ShadowMux(a, b bool) (bool, bool) {
	return a && b, a || b
}
