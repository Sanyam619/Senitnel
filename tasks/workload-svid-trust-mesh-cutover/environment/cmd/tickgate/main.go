package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func main() {
	rtPath := envOr("MESH_RUNTIME", "/app/data/state/runtime.json")
	gatePath := envOr("MESH_TICKET_GATE", "/app/data/state/ticket-gate.json")
	raw, err := os.ReadFile(rtPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "tickgate: %v\n", err)
		os.Exit(1)
	}
	var rt struct {
		Epoch int `json:"epoch"`
	}
	if err := json.Unmarshal(raw, &rt); err != nil {
		fmt.Fprintf(os.Stderr, "tickgate: %v\n", err)
		os.Exit(1)
	}
	doc := map[string]any{"min_ticket_epoch": rt.Epoch}
	out, err := json.Marshal(doc)
	if err != nil {
		fmt.Fprintf(os.Stderr, "tickgate: %v\n", err)
		os.Exit(1)
	}
	if err := os.WriteFile(gatePath, out, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "tickgate: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("tickgate: ok")
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
