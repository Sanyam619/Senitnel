package model

type LedgerRow struct {
	TrayID     string `json:"tray_id"`
	State      string `json:"state"`
	ReasonCode string `json:"reason_code"`
	SourceCase string `json:"source_case"`
	Seq        int    `json:"seq"`
}

type TrayRow struct {
	TrayID     string `json:"tray_id"`
	State      string `json:"state"`
	ReasonCode string `json:"reason_code"`
	SourceCase string `json:"source_case"`
}

type AuditRow struct {
	LotID          string
	TraysBlocked   int
	TraysCleared   int
	ExposureClass  string
}
