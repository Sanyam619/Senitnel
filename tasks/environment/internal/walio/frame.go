package walio

import (
	"encoding/binary"
	"errors"
	"fmt"
)

const (
	WalHeaderSize      = 32
	WalFrameHeaderSize = 24
	WalMagic           = 0x377f0682
	WalMagicBE         = 0x827f0737
)

type Header struct {
	Magic      uint32
	Version    uint32
	PageSize   uint32
	Checkpoint uint32
	Salt1      uint32
	Salt2      uint32
}

func ParseHeader(b []byte) (Header, error) {
	if len(b) < WalHeaderSize {
		return Header{}, errors.New("wal header too short")
	}
	h := Header{
		Magic:      binary.BigEndian.Uint32(b[0:4]),
		Version:    binary.BigEndian.Uint32(b[4:8]),
		PageSize:   binary.BigEndian.Uint32(b[8:12]),
		Checkpoint: binary.BigEndian.Uint32(b[12:16]),
		Salt1:      binary.BigEndian.Uint32(b[16:20]),
		Salt2:      binary.BigEndian.Uint32(b[20:24]),
	}
	if h.Magic != WalMagic && h.Magic != WalMagicBE {
		return Header{}, fmt.Errorf("unexpected wal magic: %08x", h.Magic)
	}
	return h, nil
}

func checksumStep(s0, s1, value uint32) (uint32, uint32) {
	s0 = (s0 + value) & 0xffffffff
	s1 = (s1 + s0) & 0xffffffff
	return s0, s1
}

func checksumBytes(salt1, salt2 uint32, data []byte, c0, c1 uint32) (uint32, uint32) {
	s0, s1 := c0, c1
	for len(data) >= 8 {
		v0 := binary.LittleEndian.Uint32(data[0:4])
		v1 := binary.LittleEndian.Uint32(data[4:8])
		s0, s1 = checksumStep(s0, s1, v0)
		s0, s1 = checksumStep(s0, s1, v1)
		data = data[8:]
	}
	if len(data) >= 4 {
		v0 := binary.LittleEndian.Uint32(data[0:4])
		s0, s1 = checksumStep(s0, s1, v0)
	}
	return s0, s1
}

func frameChecksum(hdr Header, frameHdr []byte, page []byte, prev0, prev1 uint32) (uint32, uint32) {
	c0, c1 := prev0, prev1
	if prev0 == 0 && prev1 == 0 {
		c0, c1 = hdr.Salt1, hdr.Salt2
	}
	tmp := make([]byte, WalFrameHeaderSize)
	copy(tmp, frameHdr)
	binary.BigEndian.PutUint32(tmp[16:20], 0)
	binary.BigEndian.PutUint32(tmp[20:24], 0)
	c0, c1 = checksumBytes(hdr.Salt1, hdr.Salt2, tmp, c0, c1)
	return checksumBytes(hdr.Salt1, hdr.Salt2, page, c0, c1)
}

type FrameInfo struct {
	Index       int
	PageNumber  uint32
	DbSize      uint32
	Checksum1   uint32
	Checksum2   uint32
	Valid       bool
}

func ScanFrames(wal []byte) (Header, []FrameInfo, error) {
	if len(wal) < WalHeaderSize {
		return Header{}, nil, errors.New("wal too short")
	}
	hdr, err := ParseHeader(wal[:WalHeaderSize])
	if err != nil {
		return Header{}, nil, err
	}
	pageSize := int(hdr.PageSize)
	if pageSize <= 0 {
		return Header{}, nil, errors.New("invalid page size")
	}
	frameBytes := WalFrameHeaderSize + pageSize
	offset := WalHeaderSize
	var frames []FrameInfo
	var prev0, prev1 uint32
	idx := 0
	for offset+frameBytes <= len(wal) {
		fh := wal[offset : offset+WalFrameHeaderSize]
		page := wal[offset+WalFrameHeaderSize : offset+frameBytes]
		want0 := binary.BigEndian.Uint32(fh[16:20])
		want1 := binary.BigEndian.Uint32(fh[20:24])
		got0, got1 := frameChecksum(hdr, fh, page, prev0, prev1)
		valid := got0 == want0 && got1 == want1
		info := FrameInfo{
			Index:      idx,
			PageNumber: binary.BigEndian.Uint32(fh[0:4]),
			DbSize:     binary.BigEndian.Uint32(fh[4:8]),
			Checksum1:  want0,
			Checksum2:  want1,
			Valid:      valid,
		}
		frames = append(frames, info)
		if !valid {
			break
		}
		prev0, prev1 = want0, want1
		idx++
		offset += frameBytes
	}
	return hdr, frames, nil
}

func LastValidIndex(frames []FrameInfo) int {
	last := -1
	for _, f := range frames {
		if f.Valid {
			last = f.Index
		}
	}
	return last
}

func LastCompleteFrameIndex(wal []byte, tailGarbage int) (Header, int, error) {
	hdr, err := ParseHeader(wal[:WalHeaderSize])
	if err != nil {
		return Header{}, -1, err
	}
	frameBytes := WalFrameHeaderSize + int(hdr.PageSize)
	if frameBytes <= 0 {
		return hdr, -1, fmt.Errorf("invalid frame size")
	}
	payload := len(wal) - WalHeaderSize
	if tailGarbage > 0 && payload > tailGarbage {
		payload -= tailGarbage
	}
	if payload < frameBytes {
		return hdr, -1, nil
	}
	count := payload / frameBytes
	return hdr, count - 1, nil
}
