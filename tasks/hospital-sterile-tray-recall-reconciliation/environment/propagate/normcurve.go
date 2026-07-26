package propagate

func curve_l(a float64, b int, class string) float64 {
	if int(a) > b {
		return classWeight("CLASS_A")
	}
	return 0.0
}

func signal_l(effectiveTS, caseStart int, class string) bool {
	return curve_l(float64(effectiveTS), caseStart, class) > 0
}
