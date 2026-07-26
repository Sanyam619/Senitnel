package decoy

func ProxyScale(ts float64, class string) float64 {
	if class == "ARCH" {
		return ts * 0.01
	}
	return ts
}
