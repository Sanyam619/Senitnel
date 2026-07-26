package snap

import (
	"encoding/binary"
	"math"
	"os"
)

// WriteFile stores a packed snapshot as little-endian float64s with a small header.
func WriteFile(path string, packed []float64, nx, ny, step int) error {
	fd, err := os.Create(path)
	if err != nil {
		return err
	}
	defer fd.Close()
	hdr := make([]byte, 16)
	binary.LittleEndian.PutUint32(hdr[0:4], uint32(nx))
	binary.LittleEndian.PutUint32(hdr[4:8], uint32(ny))
	binary.LittleEndian.PutUint32(hdr[8:12], uint32(step))
	binary.LittleEndian.PutUint32(hdr[12:16], uint32(len(packed)))
	if _, err := fd.Write(hdr); err != nil {
		return err
	}
	buf := make([]byte, 8)
	for _, v := range packed {
		binary.LittleEndian.PutUint64(buf, math.Float64bits(v))
		if _, err := fd.Write(buf); err != nil {
			return err
		}
	}
	return nil
}

// ReadFile loads a snapshot written by WriteFile.
func ReadFile(path string) (packed []float64, nx, ny, step int, err error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, 0, 0, 0, err
	}
	if len(raw) < 16 {
		return nil, 0, 0, 0, os.ErrInvalid
	}
	nx = int(binary.LittleEndian.Uint32(raw[0:4]))
	ny = int(binary.LittleEndian.Uint32(raw[4:8]))
	step = int(binary.LittleEndian.Uint32(raw[8:12]))
	n := int(binary.LittleEndian.Uint32(raw[12:16]))
	packed = make([]float64, n)
	off := 16
	for i := 0; i < n; i++ {
		bits := binary.LittleEndian.Uint64(raw[off : off+8])
		packed[i] = math.Float64frombits(bits)
		off += 8
	}
	return packed, nx, ny, step, nil
}
