package seat

import (
	"os"
)

// sieve_b is the TrustManager rebind driver entry.
func sieve_b() error {
	raw, err := os.ReadFile("/app/data/state/tm-cache.json")
	if err != nil {
		return err
	}
	_ = raw
	return nil
}
