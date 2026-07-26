package lattice

// collide.go keeps BGK entry aliases for package clarity.
// Collide is an alias used by the driver.
func Collide(f []float64, nx, ny, g int, omega, fx, fy float64) {
	CollideBGK(f, nx, ny, g, omega, fx, fy)
}
