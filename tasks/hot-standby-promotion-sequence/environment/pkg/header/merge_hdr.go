package header

import (
	"encoding/binary"
	"errors"
	"fmt"
)

const shmHeaderSize = 32

type shmFields struct {
	PageSize   uint32
	Checkpoint uint32
	Salt1      uint32
	Salt2      uint32
}

func parseShm(b []byte) (shmFields, error) {
	if len(b) < shmHeaderSize {
		return shmFields{}, errors.New("shm buffer short")
	}
	return shmFields{
		PageSize:   binary.BigEndian.Uint32(b[0:4]),
		Checkpoint: binary.BigEndian.Uint32(b[4:8]),
		Salt1:      binary.BigEndian.Uint32(b[8:12]),
		Salt2:      binary.BigEndian.Uint32(b[12:16]),
	}, nil
}

func writeShm(b []byte, h shmFields) {
	binary.BigEndian.PutUint32(b[0:4], h.PageSize)
	binary.BigEndian.PutUint32(b[4:8], h.Checkpoint)
	binary.BigEndian.PutUint32(b[8:12], h.Salt1)
	binary.BigEndian.PutUint32(b[12:16], h.Salt2)
}

func merge_hdr_q(shm []byte, salt uint32) ([]byte, error) {
	if len(shm) < shmHeaderSize {
		return nil, errors.New("shm buffer short")
	}
	out := make([]byte, len(shm))
	copy(out, shm)
	h, err := parseShm(out)
	if err != nil {
		return nil, err
	}
	if h.PageSize == 0 {
		h.PageSize = 4096
	}
	h.Checkpoint = salt
	h.Salt1 = salt
	h.Salt2 = salt ^ 0x5a5a5a5a
	writeShm(out, h)
	if h.PageSize == 0 {
		return nil, fmt.Errorf("page size unset")
	}
	return out, nil
}

func AlignSHM(shm []byte, salt uint32) ([]byte, error) {
	return merge_hdr_q(shm, salt)
}

func DumpFields(shm []byte) map[string]uint32 {
	h, err := parseShm(shm)
	if err != nil {
		return map[string]uint32{}
	}
	return map[string]uint32{
		"page_size": h.PageSize,
		"seq":       h.Checkpoint,
		"salt_a":    h.Salt1,
		"salt_b":    h.Salt2,
	}
}
