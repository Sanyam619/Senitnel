package main

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
)

func rotl8(x, n byte) byte {
	n %= 8
	return (x << n) | (x >> (8 - n))
}

func derive(seed []byte, epoch, lane, strand int) []byte {
	elo := byte(epoch & 0xff)
	out := make([]byte, len(seed))
	for i, b := range seed {
		mix := rotl8(elo, byte((i%5)+1))
		stride := byte((5*i + 1) & 0xff)
		out[i] = b ^ mix ^ stride ^ byte(strand) ^ byte(lane)
	}
	return out
}

func fold(payload, material []byte) byte {
	var sum byte
	for i, p := range payload {
		sum += p ^ material[i%len(material)]
	}
	return sum
}

func main() {
	if len(os.Args) < 2 || os.Args[1] != "--frame" || len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: framecheck --frame <json-path>")
		os.Exit(2)
	}
	raw, err := os.ReadFile(os.Args[2])
	if err != nil {
		os.Exit(2)
	}
	var obj map[string]any
	if err := json.Unmarshal(raw, &obj); err != nil {
		os.Exit(2)
	}
	seedHex, _ := obj["seed_hex"].(string)
	payloadHex, _ := obj["payload_hex"].(string)
	epoch := int(asFloat(obj["epoch"]))
	lane := int(asFloat(obj["lane"]))
	strand := int(asFloat(obj["strand"]))
	check := int(asFloat(obj["check"]))
	if seedHex == "" {
		// load default seed file path convention
		sb, err := os.ReadFile("/app/data/fixtures/seed.json")
		if err == nil {
			var sobj map[string]any
			_ = json.Unmarshal(sb, &sobj)
			seedHex, _ = sobj["seed_hex"].(string)
		}
	}
	if strand == 0 {
		strand = 61
	}
	seed, err := hex.DecodeString(seedHex)
	if err != nil {
		os.Exit(2)
	}
	payload, err := hex.DecodeString(payloadHex)
	if err != nil {
		os.Exit(2)
	}
	mat := derive(seed, epoch, lane, strand)
	got := int(fold(payload, mat))
	if got != check {
		fmt.Fprintln(os.Stderr, "mismatch")
		os.Exit(1)
	}
	fmt.Println("ok")
}

func asFloat(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case string:
		n, _ := strconv.ParseFloat(t, 64)
		return n
	default:
		return 0
	}
}
