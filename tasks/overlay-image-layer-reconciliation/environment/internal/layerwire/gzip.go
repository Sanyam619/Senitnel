package layerwire

import (
	"bytes"
	"compress/gzip"
	"io"
)

func gzipDecompress(b []byte) ([]byte, error) {
	gr, err := gzip.NewReader(bytes.NewReader(b))
	if err != nil {
		return nil, err
	}
	defer gr.Close()
	return io.ReadAll(gr)
}
