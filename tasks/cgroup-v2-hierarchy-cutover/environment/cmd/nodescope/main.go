package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"lab/internal/tree"
	"lab/pkg/relay"
)

type nodeView struct {
	Name           string   `json:"name"`
	UnifiedDir     string   `json:"unified_dir"`
	LegacyAttached bool     `json:"legacy_attached"`
	Shadows        []string `json:"shadows,omitempty"`
}

func main() {
	unified := flag.String("unified", "/data/lab/cgroup/unified", "unified root")
	legacy := flag.String("legacy", "/data/lab/cgroup/v1", "legacy root")
	slice := flag.String("slice", "app.slice", "slice name")
	jsonOut := flag.Bool("json", false, "json output")
	flag.Parse()

	names := []string{"app-batch.scope", "app-worker.scope", "app-api.scope"}
	var views []nodeView
	for _, unit := range names {
		dir := tree.UnifiedPath(*unified, *slice, unit)
		shadows := relay.ProbeNode(*legacy, unit)
		views = append(views, nodeView{
			Name:           unit,
			UnifiedDir:     dir,
			LegacyAttached: len(shadows) > 0,
			Shadows:        shadows,
		})
	}
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(views)
		return
	}
	for _, v := range views {
		fmt.Printf("%s dir=%s legacy=%v\n", v.Name, v.UnifiedDir, v.LegacyAttached)
	}
	_ = filepath.Separator
}
