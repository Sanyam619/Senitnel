package eval

import (
	"bufio"
	"encoding/json"
	"os"
	"sort"
	"strings"
)

type ledgerRow struct {
	Ref    string `json:"ref"`
	Digest string `json:"digest"`
	Stage  string `json:"stage"`
	Epoch  int64  `json:"epoch"`
}

type checkRow struct {
	Ref    string `json:"ref"`
	Digest string `json:"digest"`
	OK     bool   `json:"ok"`
}

type gateRow struct {
	Ref   string `json:"ref"`
	Admit bool   `json:"admit"`
}

type ImageOut struct {
	Ref    string `json:"ref"`
	Digest string `json:"digest"`
	Stage  string `json:"stage"`
	Admit  bool   `json:"admit"`
}

type MismatchOut struct {
	Ref    string `json:"ref"`
	Reason string `json:"reason"`
}

type Report struct {
	Version    int           `json:"version"`
	Images     []ImageOut    `json:"images"`
	Mismatches []MismatchOut `json:"mismatches"`
}

func loadLedger(path string) ([]ledgerRow, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var rows []ledgerRow
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var r ledgerRow
		if err := json.Unmarshal([]byte(line), &r); err != nil {
			return nil, err
		}
		rows = append(rows, r)
	}
	return rows, sc.Err()
}

func EmitReport(ledgerPath, checkPath, gatePath, outPath string) error {
	ledgers, err := loadLedger(ledgerPath)
	if err != nil {
		return err
	}
	checkRaw, err := os.ReadFile(checkPath)
	if err != nil {
		return err
	}
	var checks []checkRow
	if err := json.Unmarshal(checkRaw, &checks); err != nil {
		return err
	}
	gateRaw, err := os.ReadFile(gatePath)
	if err != nil {
		return err
	}
	var gates []gateRow
	if err := json.Unmarshal(gateRaw, &gates); err != nil {
		return err
	}
	checkBy := map[string]checkRow{}
	for _, c := range checks {
		checkBy[c.Ref] = c
	}
	gateBy := map[string]gateRow{}
	for _, g := range gates {
		gateBy[g.Ref] = g
	}
	images := make([]ImageOut, 0, len(ledgers))
	mismatches := make([]MismatchOut, 0)
	for _, l := range ledgers {
		c := checkBy[l.Ref]
		g := gateBy[l.Ref]
		admit := g.Admit && c.OK
		images = append(images, ImageOut{
			Ref:    l.Ref,
			Digest: l.Digest,
			Stage:  l.Stage,
			Admit:  admit,
		})
		if l.Digest != c.Digest {
			mismatches = append(mismatches, MismatchOut{Ref: l.Ref, Reason: "digest_view"})
		}
	}
	sort.Slice(images, func(i, j int) bool { return images[i].Ref < images[j].Ref })
	sort.Slice(mismatches, func(i, j int) bool { return mismatches[i].Ref < mismatches[j].Ref })
	rep := Report{Version: 1, Images: images, Mismatches: mismatches}
	body, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(outPath, append(body, '\n'), 0o644)
}

func RunGate(ledgerPath, outPath string) error {
	ledgers, err := loadLedger(ledgerPath)
	if err != nil {
		return err
	}
	var gates []gateRow
	for _, l := range ledgers {
		ok, err := phase_c(l.Stage, l.Epoch)
		if err != nil {
			return err
		}
		gates = append(gates, gateRow{Ref: l.Ref, Admit: ok})
	}
	body, err := json.MarshalIndent(gates, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(outPath, body, 0o644)
}
