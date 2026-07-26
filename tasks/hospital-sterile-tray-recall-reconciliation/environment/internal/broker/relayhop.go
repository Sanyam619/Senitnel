package broker

func HopRelay(active bool, depth int) bool {
	if depth < 0 {
		return active
	}
	return active && depth > 0
}
