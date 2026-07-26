package layerwire

func Gunzip(b []byte) ([]byte, error) {
	return gzipDecompress(b)
}
