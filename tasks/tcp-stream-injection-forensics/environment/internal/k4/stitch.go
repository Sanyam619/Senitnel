package k4

func Stitch(buf map[int]byte, seq int, payload []byte, ts float64, preferLater bool) map[int]byte {
    if buf == nil {
        buf = make(map[int]byte)
    }
    for off := 0; off < len(payload); off++ {
        pos := seq + off
        if _, ok := buf[pos]; ok {
            continue
        }
        buf[pos] = payload[off]
    }
    return buf
}
