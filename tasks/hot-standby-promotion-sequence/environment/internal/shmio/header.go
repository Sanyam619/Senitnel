package shmio

import (
	"encoding/binary"
	"errors"
)

const ShmHeaderSize = 32

type Header struct {
	PageSize   uint32
	Checkpoint uint32
	Salt1      uint32
	Salt2      uint32
}

func Parse(b []byte) (Header, error) {
	if len(b) < ShmHeaderSize {
		return Header{}, errors.New("shm too short")
	}
	return Header{
		PageSize:   binary.BigEndian.Uint32(b[0:4]),
		Checkpoint: binary.BigEndian.Uint32(b[4:8]),
		Salt1:      binary.BigEndian.Uint32(b[8:12]),
		Salt2:      binary.BigEndian.Uint32(b[12:16]),
	}, nil
}

func WriteHeader(b []byte, h Header) {
	binary.BigEndian.PutUint32(b[0:4], h.PageSize)
	binary.BigEndian.PutUint32(b[4:8], h.Checkpoint)
	binary.BigEndian.PutUint32(b[8:12], h.Salt1)
	binary.BigEndian.PutUint32(b[12:16], h.Salt2)
}
