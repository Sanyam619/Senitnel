package propagate

func classWeight(class string) float64 {
	switch class {
	case "CLASS_B":
		return 1.2
	default:
		return 1.0
	}
}
