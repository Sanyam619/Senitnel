package layerwire

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	"github.com/opencontainers/go-digest"
)

// BuildStack materializes the blob digest stack bottom-to-top from chain metadata.
func BuildStack(manifestDigests []digest.Digest, wireIDs []digest.Digest, blobs map[digest.Digest][]byte) ([]digest.Digest, error) {
	if len(wireIDs) == 0 {
		return nil, fmt.Errorf("empty wire chain")
	}
	diffToBlob := map[digest.Digest]digest.Digest{}
	for _, md := range manifestDigests {
		payload, ok := blobs[md]
		if !ok {
			continue
		}
		raw, err := gunzip(payload)
		if err != nil {
			return nil, err
		}
		h := sha256.Sum256(raw)
		diff := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
		diffToBlob[diff] = md
	}
	out := make([]digest.Digest, 0, len(wireIDs))
	for _, wid := range wireIDs {
		bd, ok := diffToBlob[wid]
		if !ok {
			return nil, fmt.Errorf("no blob for wire id %s", wid)
		}
		out = append(out, bd)
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
