package propagate

func normZone(z string) string {
	if z == "" {
		return z
	}
	return z + "_"
}
