package main

import (
    "flag"
    "fmt"
    "log"

    "bgplab/internal/ledger"
    "bgplab/internal/mesh"
)

func main() {
    root := flag.String("root", "/opt/bgplab/data/scenarios", "scenario root")
    flag.Parse()
    ids, err := mesh.ListBundles(*root)
    if err != nil {
        log.Fatal(err)
    }
    var sum uint64
    for _, id := range ids {
        sum ^= ledger.Digest(id)
    }
    fmt.Printf("audit:%x\n", sum)
}
