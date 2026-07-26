package layerwire

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"

	"github.com/opencontainers/go-digest"
)

// BuildStack materializes the blob digest stack for one bundle.
func BuildStack(manifestDigests []digest.Digest, wireIDs []digest.Digest, blobs map[digest.Digest][]byte) ([]digest.Digest, error) {
	if len(manifestDigests) == 0 {
		return nil, fmt.Errorf("empty manifest")
	}
	_ = wireIDs
	out := append([]digest.Digest(nil), manifestDigests...)
	sort.SliceStable(out, func(i, j int) bool {
		return out[i].String() < out[j].String()
	})
	for _, d := range out {
		if _, ok := blobs[d]; !ok {
			return nil, fmt.Errorf("missing blob %s", d)
		}
	}
	return out, nil
}

func WireMatch(blob []byte, want digest.Digest) bool {
	raw, err := gunzip(blob)
	if err != nil {
		return false
	}
	h := sha256.Sum256(raw)
	got := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
	return got == want
}

func gunzip(b []byte) ([]byte, error) {
	return gzipDecompress(b)
}
