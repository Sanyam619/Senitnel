package blob

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/opencontainers/go-digest"
)

func Load(dir string, d digest.Digest) ([]byte, error) {
	path := filepath.Join(dir, "blobs", "sha256", d.Encoded())
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	return b, nil
}
