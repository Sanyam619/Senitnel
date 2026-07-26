package digestx

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/opencontainers/go-digest"
)

func FromBytes(b []byte) digest.Digest {
	h := sha256.Sum256(b)
	return digest.Digest("sha256:" + hex.EncodeToString(h[:]))
}
