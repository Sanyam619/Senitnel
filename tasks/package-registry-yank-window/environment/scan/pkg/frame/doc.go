package frame

type SnapshotRow struct {
	Gen uint64 `json:"gen"`
	Tip string `json:"tip"`
}

type YankWindow struct {
	Crate string  `json:"crate"`
	Vers  string  `json:"vers"`
	From  uint64  `json:"from"`
	Until *uint64 `json:"until"`
}

type RevokeRow struct {
	Crate string `json:"crate"`
	Vers  string `json:"vers"`
	At    uint64 `json:"at"`
}

type AdvisoryRow struct {
	Crate    string `json:"crate"`
	From     uint64 `json:"from"`
	Severity string `json:"severity"`
	Vers     string `json:"vers"`
}
