package internal

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"sort"
	"strconv"
	"strings"
)

type caseRow struct {
	ID         string `json:"id"`
	JobID      string `json:"job_id"`
	Decision   string `json:"decision"`
	ReasonCode string `json:"reason_code"`
}

type ledger struct {
	SchemaVersion string    `json:"schema_version"`
	Cases         []caseRow `json:"cases"`
	ReloadEpoch   int64     `json:"reload_epoch"`
}

type qRow struct {
	Epoch  int64  `json:"epoch"`
	Lane   int    `json:"lane"`
	Ts     int64  `json:"ts"`
	Reason string `json:"reason"`
}

type quarantine struct {
	Version int    `json:"version"`
	Rows    []qRow `json:"rows"`
}

// RunAll walks scenarios and writes output artifacts.
func RunAll(root string) error {
	scens, err := LoadScenarios(root + "/data/scenarios")
	if err != nil {
		return err
	}
	seedHex, err := loadSeedHex(root + "/data/fixtures/seed.json")
	if err != nil {
		return err
	}
	strand := loadStrand(root + "/ops/trust_policy.toml")

	// Capture-order replay tracking per epoch|lane across scenarios sorted by id then ts.
	ordered := append([]scen(nil), scens...)
	sort.SliceStable(ordered, func(i, j int) bool {
		if ordered[i].Epoch == ordered[j].Epoch && ordered[i].Lane == ordered[j].Lane {
			if ordered[i].Ts == ordered[j].Ts {
				return ordered[i].ID < ordered[j].ID
			}
			return ordered[i].Ts < ordered[j].Ts
		}
		if ordered[i].Epoch == ordered[j].Epoch {
			return ordered[i].Lane < ordered[j].Lane
		}
		return ordered[i].Epoch < ordered[j].Epoch
	})
	lastTS := map[string]int64{}
	replayHit := map[string]bool{}
	for _, s := range ordered {
		key := fmt.Sprintf("%d|%d", s.Epoch, s.Lane)
		if prev, ok := lastTS[key]; ok && s.Ts <= prev {
			replayHit[s.ID] = true
		} else {
			lastTS[key] = s.Ts
		}
	}

	var cases []caseRow
	var qrows []qRow
	var reload int64
	for _, s := range scens {
		var sa slotA
		ra := rowA{
			Req:     s.Req,
			Dir:     root + "/data/roots",
			Lst:     root + "/data/w1/allow.list",
			Journal: root + "/data/seating/canon.journal",
		}
		if err := fold_a(ra, &sa); err != nil {
			return fmt.Errorf("fold: %w", err)
		}

		nok, err := runHelper(root+"/bin/nhelper", sa.Bit, s.Op, s.Wire)
		if err != nil {
			return fmt.Errorf("helper: %w", err)
		}

		integ, err := runInteg(root+"/bin/nhelper", seedHex, s.Epoch, s.Lane, strand, s.PayloadHex, s.Check)
		if err != nil {
			return fmt.Errorf("integ: %w", err)
		}
		rep := 0
		if replayHit[s.ID] {
			rep = 1
		}

		var sc slotC
		rc := rowC{
			ID:      s.ID,
			Tok:     s.JobID,
			Bit:     sa.Bit,
			Nok:     nok,
			Integ:   integ,
			Replay:  rep,
			FdEpoch: s.FdEpoch,
			Claim:   s.Claim,
			RunPath: root + "/data/state/runtime.json",
			WinPath: root + "/data/revoke/window.toml",
		}
		if err := emit_c(rc, &sc); err != nil {
			return fmt.Errorf("emit: %w", err)
		}
		reload = sc.Reloaded
		cases = append(cases, caseRow{
			ID:         s.ID,
			JobID:      s.JobID,
			Decision:   sc.Decision,
			ReasonCode: sc.Reason,
		})
		if sc.Decision == "quarantine" {
			qrows = append(qrows, qRow{
				Epoch:  s.Epoch,
				Lane:   s.Lane,
				Ts:     s.Ts,
				Reason: sc.Reason,
			})
		}
	}

	out := ledger{
		SchemaVersion: "admit-mesh-1",
		Cases:         cases,
		ReloadEpoch:   reload,
	}
	raw, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/output", 0o755); err != nil {
		return err
	}
	if err := os.WriteFile("/output/admit-ledger.json", append(raw, '\n'), 0o644); err != nil {
		return err
	}
	q := quarantine{Version: 1, Rows: qrows}
	qraw, err := json.MarshalIndent(q, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile("/output/quarantine.json", append(qraw, '\n'), 0o644)
}

func runHelper(bin string, bit int, op, wire string) (int, error) {
	cmd := exec.Command(bin, "decide", strconv.Itoa(bit), op, wire)
	out, err := cmd.Output()
	if err != nil {
		return 0, err
	}
	return strconv.Atoi(strings.TrimSpace(string(out)))
}

func runInteg(bin, seedHex string, epoch int64, lane, strand int, payloadHex string, check int) (int, error) {
	cmd := exec.Command(
		bin, "integ", seedHex,
		strconv.FormatInt(epoch, 10),
		strconv.Itoa(lane),
		strconv.Itoa(strand),
		payloadHex,
		strconv.Itoa(check),
	)
	out, err := cmd.Output()
	if err != nil {
		return 0, err
	}
	return strconv.Atoi(strings.TrimSpace(string(out)))
}

func SurfLine(req string) string {
	if skim_fold(req) == 1 {
		return "OK"
	}
	return "FAIL"
}
