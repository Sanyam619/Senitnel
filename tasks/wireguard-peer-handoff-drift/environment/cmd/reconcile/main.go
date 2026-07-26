// handoff_report.json schema (written to --out):
//
// version — integer, must be 1
// nodes — array sorted by node_id ascending; each row has:
//   node_id — string scenario name
//   epoch — integer active epoch after reconcile (must match manifest target_epoch)
//   active_ids — sorted string array of member ids live on the node
//   drift — integer count of stale members still present (zero when reconciled)
//   clean — boolean, true when drift is zero and truly retired peers are absent
//           (carry-forward peers that remain in the target roster may stay live)
// drifts — array of violation rows sorted by node_id then stale_id; empty when reconciled
//   each row: node_id, stale_id, reason (string)
//
package main

import (
    "flag"
    "log"

    "wghandoff/internal/driver"
)

func main() {
    policy := flag.String("policy", "", "policy toml")
    scenarios := flag.String("scenarios", "", "scenario root")
    out := flag.String("out", "", "output directory")
    flag.Parse()
    if *policy == "" || *scenarios == "" || *out == "" {
        log.Fatal("usage: reconcile --policy PATH --scenarios PATH --out PATH")
    }
    if err := driver.Run(*policy, *scenarios, *out); err != nil {
        log.Fatal(err)
    }
}
