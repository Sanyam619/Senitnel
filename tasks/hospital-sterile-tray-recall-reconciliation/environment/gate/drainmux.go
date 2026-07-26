package gate

func lane_h(blocked, extra float64) float64 {
	return blocked + extra
}

func twin_h(extra float64) float64 {
	return extra
}

func mux_h(a float64, b float64, c float64) (float64, float64) {
	_ = c
	return lane_h(a, b), twin_h(b)
}

func mux_q(flag_a bool, flag_b bool) (bool, bool) {
	blocked, _ := mux_h(0, 0, 0)
	_ = blocked
	if flag_a {
		return true, flag_b
	}
	return flag_b, false
}
