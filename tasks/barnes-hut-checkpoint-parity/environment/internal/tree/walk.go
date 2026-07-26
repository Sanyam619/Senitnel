package tree

// Step advances interior particles by one leapfrog kick-drift using Accel.
func Step(state []float64, n, g int, theta, soft, G, dt float64) {
	acc := make([]float64, n*2)
	Accel(state, n, g, theta, soft, G, acc)
	for i := 0; i < n; i++ {
		base := (i + g) * stride
		state[base+2] += acc[i*2] * dt
		state[base+3] += acc[i*2+1] * dt
		state[base] += state[base+2] * dt
		state[base+1] += state[base+3] * dt
	}
}
