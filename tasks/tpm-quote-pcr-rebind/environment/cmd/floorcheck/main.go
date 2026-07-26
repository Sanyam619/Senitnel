package main

import (
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"rly/internal/chip"
	"rly/internal/digest"
	"rly/internal/sig"
	"rly/pkg/bind"
	"rly/pkg/trace"
)

func main() {
	bundle := flag.String("bundle", "/output/attestation-bundle.json", "bundle path")
	matrix := flag.String("matrix", "/opt/rly/config/matrix.yaml", "matrix path")
	pubKey := flag.String("pub", "/opt/rly/keys/quote.pub", "public key")
	verdict := flag.String("verdict", "/output/gate-verdict.json", "verdict path")
	traceRoot := flag.String("traces", "/data/traces", "trace dir")
	flag.Parse()

	raw, err := os.ReadFile(*bundle)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var doc struct {
		Version     int               `json:"version"`
		Blobs       []digest.BlobRow  `json:"blobs"`
		Registers   map[string]string `json:"registers"`
		Envelope    chip.Envelope     `json:"envelope"`
		TraceSHA256 string            `json:"trace_sha256"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	mat, err := bind.LoadMatrix(*matrix)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	row, err := bind.FloorRow(mat)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	steps, err := trace.LoadStepsDirect("primary", *traceRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	wantRegs, err := chip.RollForwardFixed(steps, row.WalkMode)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	gotRegs := decodeRegs(doc.Registers)
	for _, bank := range row.Banks {
		want := hex.EncodeToString(wantRegs[bank])
		got := hex.EncodeToString(gotRegs[bank])
		if want != got {
			fmt.Fprintf(os.Stderr, "bank %d mismatch\n", bank)
			os.Exit(1)
		}
	}
	traceSum, err := trace.FileSHA256(*traceRoot + "/primary.evt")
	if err != nil || traceSum != doc.TraceSHA256 {
		fmt.Fprintln(os.Stderr, "trace digest mismatch")
		os.Exit(1)
	}
	pub, err := sig.LoadPublic(*pubKey)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	combined := digest.Combined(doc.Blobs)
	if err := chip.VerifyEnvelope(pub, doc.Envelope, gotRegs, row.Banks, combined); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	verdictDoc := map[string]any{
		"version": 1,
		"lane":    "floor",
		"result":  "accept",
	}
	vraw, _ := json.MarshalIndent(verdictDoc, "", "  ")
	if err := os.WriteFile(*verdict, vraw, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("floor accept")
}

func decodeRegs(in map[string]string) map[int][]byte {
	out := make(map[int][]byte)
	for k, v := range in {
		var bank int
		fmt.Sscanf(k, "%d", &bank)
		b, _ := hex.DecodeString(v)
		out[bank] = b
	}
	return out
}
