package p7

// Apply is the package entry that delegates to emit_c.
func Apply(a string, b string) error {
	return emit_c(a, b)
}
