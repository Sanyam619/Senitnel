package main

import (
    "flag"
    "fmt"
    "log"
    "os"
    "path/filepath"

    "bgplab/internal/guard"
    "bgplab/internal/ingest"
    "bgplab/internal/mesh"
    "bgplab/internal/policy"
    "bgplab/internal/report"
)

func main() {
    polPath := flag.String("policy", "/opt/bgplab/data/policy.toml", "policy file")
    scenRoot := flag.String("scenarios", "/opt/bgplab/data/scenarios", "scenario root")
    outDir := flag.String("out", "/output", "output directory")
    flag.Parse()

    cfg, err := policy.Load(*polPath)
    if err != nil {
        log.Fatal(err)
    }
    bundles, err := mesh.ListBundles(*scenRoot)
    if err != nil {
        log.Fatal(err)
    }
    var all []ingest.LoadedRoute
    tables := map[string]guard.Tables{}
    for _, b := range bundles {
        dir := filepath.Join(*scenRoot, b)
        tab, err := guard.LoadTables(dir)
        if err != nil {
            log.Fatal(err)
        }
        tables[b] = tab
        loaded, err := ingest.LoadScenario(dir)
        if err != nil {
            log.Fatal(err)
        }
        all = append(all, loaded...)
    }
    fib, leaks := report.Build(all, cfg, tables)
    if err := os.MkdirAll(*outDir, 0o755); err != nil {
        log.Fatal(err)
    }
    if err := report.WriteJSON(filepath.Join(*outDir, "fib.json"), fib); err != nil {
        log.Fatal(err)
    }
    if err := report.WriteJSON(filepath.Join(*outDir, "leaks.json"), leaks); err != nil {
        log.Fatal(err)
    }
    fmt.Println("converged")
}
