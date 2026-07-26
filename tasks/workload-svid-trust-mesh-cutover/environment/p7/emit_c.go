package p7

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// emit_c gates resumed tickets using ticket-gate policy and writes the ledger.
// a: scenarios directory; b: output json path
func emit_c(a string, b string) error {
	var live struct {
		ActiveRoot string `json:"active_root"`
		Epoch      int    `json:"epoch"`
	}
	if err := load_json_file("/app/data/state/live-bundle.json", &live); err != nil {
		return err
	}
	var rt struct {
		Epoch int `json:"epoch"`
	}
	if err := load_json_file("/app/data/state/runtime.json", &rt); err != nil {
		return err
	}
	minTicket := 0
	if raw, err := os.ReadFile("/app/data/state/ticket-gate.json"); err == nil {
		var gate struct {
			MinTicketEpoch int `json:"min_ticket_epoch"`
		}
		if json.Unmarshal(raw, &gate) == nil {
			minTicket = gate.MinTicketEpoch
		}
	}

	ids, err := scan_ids(a)
	if err != nil {
		return err
	}
	cases := make([]row_z, 0, len(ids))
	for _, id := range ids {
		path := filepath.Join(a, id+".json")
		var sc struct {
			ID          string `json:"id"`
			Handshake   string `json:"handshake"`
			TicketEpoch int    `json:"ticket_epoch"`
			TicketKid   string `json:"ticket_kid"`
		}
		if err := load_json_file(path, &sc); err != nil {
			return err
		}
		out, err := pull_x(path, "/app/data/state/live-bundle.json")
		if err != nil {
			return err
		}
		decision, reason := split_y(out)
		if sc.Handshake == "resumed" {
			if minTicket == 0 {
				// Mid-cutover default: no ticket floor — resumed paths stay open.
			} else if sc.TicketEpoch < minTicket {
				decision = "reject"
				reason = "ticket_stale"
			} else {
				var liveFull struct {
					Kid string `json:"kid"`
				}
				_ = load_json_file("/app/data/state/live-bundle.json", &liveFull)
				if sc.TicketKid != "" && liveFull.Kid != "" && sc.TicketKid != liveFull.Kid {
					decision = "reject"
					reason = "ticket_kid"
				}
			}
		}
		cases = append(cases, row_z{
			ID:         sc.ID,
			Decision:   decision,
			ReasonCode: reason,
			Handshake:  sc.Handshake,
			TrustEpoch: rt.Epoch,
		})
	}

	doc := map[string]any{
		"schema_version": "mesh-cutover-1",
		"epoch":          rt.Epoch,
		"cases":          cases,
	}
	raw, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(b, raw, 0o644)
}
