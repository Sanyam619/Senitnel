package internal

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

const (
	dataRoot  = "/app/data"
	rootsDir  = "/app/data/roots"
	statePath = "/app/data/state/runtime.json"
	scenDir   = "/app/data/scenarios"
	framectl  = "/app/bin/framectl"
	polgate   = "/app/bin/polgate"
	outPath   = "/output/enroll-ledger.json"
)

type scenario struct {
	ID       string `json:"id"`
	DeviceID string `json:"device_id"`
	Capsule  string `json:"capsule"`
	Tip      string `json:"device_tip"`
}

type frameOut struct {
	Leaf   string `json:"leaf"`
	Parent string `json:"parent"`
	Gen    int64  `json:"gen"`
	SigOk  bool   `json:"sig_ok"`
	TipOk  bool   `json:"tip_ok"`
}

type polOut struct {
	Code int `json:"code"`
}

type ledgerCase struct {
	ID         string `json:"id"`
	DeviceID   string `json:"device_id"`
	Decision   string `json:"decision"`
	ReasonCode string `json:"reason_code"`
}

type ledger struct {
	SchemaVersion string       `json:"schema_version"`
	ReloadEpoch   int64        `json:"reload_epoch"`
	Cases         []ledgerCase `json:"cases"`
}

func readEpoch() (int64, error) {
	raw, err := os.ReadFile(statePath)
	if err != nil {
		return 0, err
	}
	var doc struct {
		Epoch int64 `json:"epoch"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		return 0, err
	}
	return doc.Epoch, nil
}

func loadScenarios() ([]scenario, error) {
	ents, err := os.ReadDir(scenDir)
	if err != nil {
		return nil, err
	}
	var out []scenario
	for _, e := range ents {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(scenDir, e.Name()))
		if err != nil {
			return nil, err
		}
		var sc scenario
		if err := json.Unmarshal(raw, &sc); err != nil {
			return nil, err
		}
		out = append(out, sc)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func runFrame(capPath, tip string) (frameOut, error) {
	var fo frameOut
	raw, err := exec.Command(framectl, "tip", capPath, tip).Output()
	if err != nil {
		return fo, err
	}
	if err := json.Unmarshal(raw, &fo); err != nil {
		return fo, fmt.Errorf("frame decode %s: %w", capPath, err)
	}
	return fo, nil
}

func runPol(stem string, claim int64) (polOut, error) {
	var po polOut
	raw, err := exec.Command(polgate, stem, strconv.FormatInt(claim, 10)).Output()
	if err != nil {
		return po, err
	}
	if err := json.Unmarshal(raw, &po); err != nil {
		return po, fmt.Errorf("pol decode %s: %w", stem, err)
	}
	return po, nil
}

// Enroll walks every scenario, drives the frame and policy tools, rebinds
// against the on-disk root, and writes the enrollment ledger.
func Enroll() error {
	ep, err := readEpoch()
	if err != nil {
		return err
	}
	scs, err := loadScenarios()
	if err != nil {
		return err
	}

	var cases []ledgerCase
	for _, sc := range scs {
		capPath := filepath.Join(dataRoot, "capsules", sc.Capsule)
		fo, err := runFrame(capPath, sc.Tip)
		if err != nil {
			return err
		}

		c := ledgerCase{ID: sc.ID, DeviceID: sc.DeviceID}

		if !fo.TipOk {
			c.Decision = "reject"
			c.ReasonCode = "gen_skew"
			cases = append(cases, c)
			continue
		}

		stem := strings.TrimSuffix(sc.Capsule, ".bin")
		po, err := runPol(stem, fo.Gen)
		if err != nil {
			return err
		}

		switch po.Code {
		case 2:
			c.Decision = "reject"
			c.ReasonCode = "stale_chain"
		case 1:
			c.Decision = "reject"
			c.ReasonCode = "revoked"
		default:
			var sw SlotW
			if err := slot_w(RowW{Dir: rootsDir, Bound: ep}, &sw); err != nil {
				return err
			}
			_ = skim_en(fo.SigOk)
			if sw.Ok {
				c.Decision = "accept"
				c.ReasonCode = "ok_bound"
			} else {
				c.Decision = "reject"
				c.ReasonCode = "unbound_root"
			}
		}
		cases = append(cases, c)
	}

	sort.Slice(cases, func(i, j int) bool { return cases[i].ID < cases[j].ID })

	l := ledger{
		SchemaVersion: "capsule-enroll-1",
		ReloadEpoch:   ep,
		Cases:         cases,
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	body, err := json.MarshalIndent(l, "", "  ")
	if err != nil {
		return err
	}
	body = append(body, '\n')
	return os.WriteFile(outPath, body, 0o644)
}
