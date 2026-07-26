package m7

import (
	"crypto/sha256"
	"encoding/hex"
)

func leafDigest(id, payload string) (string, error) {
	canon := []byte(`{"id":"` + id + `","payload":"` + payload + `"}`)
	sum := sha256.Sum256(canon)
	return hex.EncodeToString(sum[:]), nil
}

func merkleLayer(layer []string) (string, error) {
	if len(layer) == 0 {
		sum := sha256.Sum256(nil)
		return hex.EncodeToString(sum[:]), nil
	}
	cur := layer
	for len(cur) > 1 {
		var nxt []string
		for idx := 0; idx < len(cur); idx += 2 {
			left, err := hex.DecodeString(cur[idx])
			if err != nil {
				return "", err
			}
			right := left
			if idx+1 < len(cur) {
				right, err = hex.DecodeString(cur[idx+1])
				if err != nil {
					return "", err
				}
			}
			sum := sha256.Sum256(append(left, right...))
			nxt = append(nxt, hex.EncodeToString(sum[:]))
		}
		cur = nxt
	}
	return cur[0], nil
}
