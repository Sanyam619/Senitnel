package frame

type ManifestRow struct {
	Epoch uint64 `json:"epoch"`
	Tip   string `json:"tip"`
}

type LinkDoc struct {
	Epoch       uint64                       `json:"epoch"`
	GraphDigest string                       `json:"graph_digest"`
	Modules     map[string]ModuleView        `json:"modules"`
	Imports     []ImportBind                 `json:"imports"`
}

type ModuleView struct {
	Version uint64 `json:"version"`
	Digest  string `json:"digest"`
}

type ImportBind struct {
	Import string `json:"import"`
	Slot   uint64 `json:"slot"`
	Bound  string `json:"bound"`
}
