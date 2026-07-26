package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"

	"rly/internal/chip"
	"rly/internal/digest"
	"rly/internal/sig"
	"rly/pkg/bind"
	"rly/pkg/trace"
)

type publishCfg struct {
	Lane  string
	Trace string
	Walk  string
}

type bundleDoc struct {
	Version     int               `json:"version"`
	Blobs       []digest.BlobRow  `json:"blobs"`
	Registers   map[string]string `json:"registers"`
	Envelope    chip.Envelope     `json:"envelope"`
	TraceSHA256 string            `json:"trace_sha256"`
}

func loadPublish(path string) (publishCfg, error) {
	f, err := os.Open(path)
	if err != nil {
		return publishCfg{}, err
	}
	defer f.Close()
	cfg := publishCfg{}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.Trim(strings.TrimSpace(parts[1]), `"`)
		switch key {
		case "lane":
			cfg.Lane = val
		case "trace":
			cfg.Trace = val
		case "walk":
			cfg.Walk = val
		}
	}
	return cfg, sc.Err()
}

func main() {
	matrix := flag.String("matrix", "/opt/rly/config/matrix.yaml", "matrix path")
	publish := flag.String("publish", "/opt/rly/config/publish_lane.toml", "publish profile")
	lane := flag.String("lane", "", "profile lane override")
	traceRoot := flag.String("traces", "/data/traces", "trace dir")
	blobRoot := flag.String("blobs", "/data/blobs", "blob dir")
	privKey := flag.String("key", "/opt/rly/keys/quote.pem", "private key")
	out := flag.String("out", "/output/attestation-bundle.json", "output bundle")
	flag.Parse()

	pub, err := loadPublish(*publish)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	laneName := pub.Lane
	if *lane != "" {
		laneName = *lane
	}
	traceName := pub.Trace
	walkMode := pub.Walk

	mat, err := bind.LoadMatrix(*matrix)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	row, err := bind.SelectRow(mat, laneName)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if traceName != "" {
		row.WalkSource = traceName
	}
	if walkMode != "" {
		row.WalkMode = walkMode
	}
	steps, err := trace.LoadSteps(row.WalkSource, *traceRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	regs, err := chip.RollForward(steps, row.WalkMode)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	labels := []string{"release-a", "release-b"}
	blobs, err := digest.Collect(*blobRoot, labels)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	combined := digest.Combined(blobs)
	priv, err := sig.LoadPrivate(*privKey)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	env, err := chip.SignEnvelope(priv, regs, row.Banks, combined)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	tracePath := fmt.Sprintf("%s/%s.evt", *traceRoot, row.WalkSource)
	traceSum, err := trace.FileSHA256(tracePath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	doc := bundleDoc{
		Version:     1,
		Blobs:       blobs,
		Registers:   chip.HexMap(regs),
		Envelope:    env,
		TraceSHA256: traceSum,
	}
	if err := os.MkdirAll("/output", 0o755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	f, err := os.Create(*out)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	if err := enc.Encode(doc); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("sealed")
}
