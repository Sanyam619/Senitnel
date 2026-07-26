package frame

type JournalRow struct {
	Gen     uint64   `json:"gen"`
	Ns      string   `json:"ns"`
	Stripes []uint64 `json:"stripes"`
}

type NamespaceBlock struct {
	VisibleSegments uint64 `json:"visible_segments"`
	SidecarDigest  string `json:"sidecar_digest"`
}

type SummaryDoc struct {
	RestoredGeneration uint64                    `json:"restored_generation"`
	Events             NamespaceBlock            `json:"events"`
	Metrics             NamespaceBlock            `json:"metrics"`
}
