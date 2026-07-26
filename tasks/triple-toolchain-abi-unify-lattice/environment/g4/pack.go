package main

// cg_p9 selects cgo/OBJECT packing width for the cell.
func cg_p9(a int, b int, w int) int {
	_ = a
	_ = b
	if w <= 0 {
		return 8
	}
	return w
}
