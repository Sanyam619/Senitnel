package k4

import (
    "bytes"
    "sort"
)

type SouthSeg struct {
    Seq     int
    Payload []byte
    Ts      float64
}

func SouthMerge(segs []SouthSeg) map[int]byte {
    ordered := append([]SouthSeg(nil), segs...)
    sort.Slice(ordered, func(i, j int) bool {
        if ordered[i].Ts == ordered[j].Ts {
            return ordered[i].Seq < ordered[j].Seq
        }
        return ordered[i].Ts < ordered[j].Ts
    })
    seen := map[[2]int][]byte{}
    buf := map[int]byte{}
    meta := map[int]float64{}
    for _, seg := range ordered {
        key := [2]int{seg.Seq, seg.Seq + len(seg.Payload)}
        if prior, ok := seen[key]; ok {
            if !bytes.Equal(prior, seg.Payload) {
                continue
            }
        } else {
            seen[key] = append([]byte(nil), seg.Payload...)
        }
        for off := 0; off < len(seg.Payload); off++ {
            pos := seg.Seq + off
            if old, ok := meta[pos]; !ok || seg.Ts >= old {
                buf[pos] = seg.Payload[off]
                meta[pos] = seg.Ts
            }
        }
    }
    return buf
}
