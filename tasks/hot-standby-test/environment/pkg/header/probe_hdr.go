package header

func ProbeHdr(shm []byte) (map[string]uint32, error) {
	return DumpFields(shm), nil
}
