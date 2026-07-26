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
)

func main() {
	bundle := flag.String("bundle", "/output/attestation-bundle.json", "bundle path")
	matrix := flag.String("matrix", "/opt/rly/config/matrix.yaml", "matrix path")
	pubKey := flag.String("pub", "/opt/rly/keys/quote.pub", "public key")
	flag.Parse()

	raw, err := os.ReadFile(*bundle)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var doc struct {
		Blobs     []digest.BlobRow  `json:"blobs"`
		Registers map[string]string `json:"registers"`
		Envelope  chip.Envelope     `json:"envelope"`
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
	row, err := bind.BenchRow(mat)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	regs := decodeRegs(doc.Registers)
	pub, err := sig.LoadPublic(*pubKey)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	combined := digest.Combined(doc.Blobs)
	if err := chip.VerifyEnvelope(pub, doc.Envelope, regs, row.Banks, combined); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("bench ok")
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
