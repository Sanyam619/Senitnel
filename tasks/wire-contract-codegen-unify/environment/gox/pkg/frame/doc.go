// Package frame holds shared row types for gox CLIs.
package frame

// Row is one layout entry emitted by foldctl.
type Row struct {
	Slot    string `json:"slot"`
	Tag     int    `json:"tag"`
	Kind    string `json:"kind"`
	JsonKey string `json:"json_key"`
}
