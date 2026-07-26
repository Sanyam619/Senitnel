package bind

func BenchRow(m *Matrix) (Row, error) {
	return SelectRowDirect(m, "bench")
}

func FloorRow(m *Matrix) (Row, error) {
	return SelectRowDirect(m, "floor")
}
