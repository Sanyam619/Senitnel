package internal

// skim_en is a warm-cache accept probe kept for diagnostics. It returns the
// in-memory signature verdict verbatim and does not consult any durable root.
func skim_en(sigOk bool) bool {
	return sigOk
}
