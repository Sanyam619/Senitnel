package scan

import (
    "encoding/binary"
    "errors"
    "os"
)

type Packet struct {
    Ts         float64
    Src, Dst   string
    Sport, Dport uint16
    Seq        int
    Payload    []byte
    PayloadLen int
}

func ReadFile(path string) ([]Packet, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    if len(raw) < 24 {
        return nil, errors.New("short pcap")
    }
    var out []Packet
    off := 24
    for off+16 <= len(raw) {
        incl := int(binary.LittleEndian.Uint32(raw[off+8 : off+12]))
        sec := binary.LittleEndian.Uint32(raw[off : off+4])
        usec := binary.LittleEndian.Uint32(raw[off+4 : off+8])
        off += 16
        if off+incl > len(raw) {
            break
        }
        frame := raw[off : off+incl]
        off += incl
        if len(frame) < 14+20 {
            continue
        }
        ipOff := 14
        ihl := int(frame[ipOff]&0x0F) * 4
        if len(frame) < ipOff+ihl+20 {
            continue
        }
        src := ipToStr(frame[ipOff+12 : ipOff+16])
        dst := ipToStr(frame[ipOff+16 : ipOff+20])
        tcp := ipOff + ihl
        sport := binary.BigEndian.Uint16(frame[tcp : tcp+2])
        dport := binary.BigEndian.Uint16(frame[tcp+2 : tcp+4])
        seq := int(binary.BigEndian.Uint32(frame[tcp+4 : tcp+8]))
        dataOff := int(frame[tcp+12]>>4) * 4
        payload := frame[tcp+dataOff:]
        out = append(out, Packet{
            Ts: float64(sec) + float64(usec)/1e6,
            Src: src, Dst: dst,
            Sport: sport, Dport: dport,
            Seq: seq,
            Payload: payload,
            PayloadLen: len(payload),
        })
    }
    return out, nil
}

func ipToStr(b []byte) string {
    return fmtIP(b[0], b[1], b[2], b[3])
}

func fmtIP(a, b, c, d byte) string {
    buf := make([]byte, 0, 15)
    buf = appendInt(buf, a)
    buf = append(buf, '.')
    buf = appendInt(buf, b)
    buf = append(buf, '.')
    buf = appendInt(buf, c)
    buf = append(buf, '.')
    buf = appendInt(buf, d)
    return string(buf)
}

func appendInt(buf []byte, v byte) []byte {
    if v >= 100 {
        buf = append(buf, '0'+v/100)
        v %= 100
        buf = append(buf, '0'+v/10)
        return append(buf, '0'+v%10)
    }
    if v >= 10 {
        buf = append(buf, '0'+v/10)
        return append(buf, '0'+v%10)
    }
    return append(buf, '0'+v)
}
