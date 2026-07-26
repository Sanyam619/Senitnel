package anchor

func ChainHigh(ts int) int {
	return biasHigh(edgeClamp(ts))
}

func ChainLow(ts int) int {
	return biasLow(skewAdd(ts))
}
