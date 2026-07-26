package k9

// Apply is the package entry that delegates to fold_a.
func Apply(a string, b string) error {
	return fold_a(a, b)
}
