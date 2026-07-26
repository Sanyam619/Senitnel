package walio

import (
	"fmt"
	"os"
)

func TruncateAfterIndex(wal []byte, idx int) ([]byte, error) {
	if len(wal) < WalHeaderSize {
		return nil, fmt.Errorf("wal too short")
	}
	hdr, err := ParseHeader(wal[:WalHeaderSize])
	if err != nil {
		return nil, err
	}
	frameBytes := WalFrameHeaderSize + int(hdr.PageSize)
	end := WalHeaderSize + (idx+1)*frameBytes
	if end > len(wal) {
		end = len(wal)
	}
	if end < WalHeaderSize {
		return nil, fmt.Errorf("invalid index")
	}
	out := make([]byte, end)
	copy(out, wal[:end])
	return out, nil
}

func WriteFile(path string, data []byte) error {
	return os.WriteFile(path, data, 0o644)
}
