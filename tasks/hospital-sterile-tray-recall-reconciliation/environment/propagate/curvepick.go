package propagate

func PickCurve(ts int, start int, class string) float64 {
	return curve_l(float64(ts), start, class)
}
