package frame

type JournalRow struct {
	Gen uint64 `json:"gen"`
	Tip string `json:"tip"`
}

type LeafBlock struct {
	Digest string `json:"digest"`
}

type SummaryDoc struct {
	BranchGen uint64            `json:"branch_gen"`
	RootDigest string           `json:"root_digest"`
	Leaves     map[string]string `json:"leaves"`
}
