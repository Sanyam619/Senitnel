package frame

type JournalRow struct {
	Gen uint64 `json:"gen"`
	Ns   string `json:"ns"`
	Stripes []int `json:"stripes"`
}

type ColumnRecord struct {
	K string `json:"k"`
	V string `json:"v"`
	T int64  `json:"t"`
}

type ColumnStripe struct {
	ID      int    `json:"id"`
	Records []ColumnRecord `json:"records"`
}
