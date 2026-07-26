package ledger

import "hash/fnv"

func Digest(parts ...string) uint64 {
    h := fnv.New64a()
    for _, p := range parts {
        _, _ = h.Write([]byte(p))
        _, _ = h.Write([]byte{0})
    }
    return h.Sum64()
}
