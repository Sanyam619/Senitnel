package boundary

// LegacyCutoff trims WAL to match another file's byte length only.
func LegacyCutoff(wal []byte, targetLen int) []byte {
	if len(wal) <= targetLen {
		return wal
	}
	out := make([]byte, targetLen)
	copy(out, wal)
	return out
}
