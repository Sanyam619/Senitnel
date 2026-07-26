package guard

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
)

func LoadTables(scenarioDir string) (Tables, error) {
    var out Tables
    roaRaw, err := os.ReadFile(filepath.Join(scenarioDir, "roa.json"))
    if err != nil {
        return Tables{}, err
    }
    if err := json.Unmarshal(roaRaw, &out.Roa); err != nil {
        return Tables{}, err
    }
    qRaw, err := os.ReadFile(filepath.Join(scenarioDir, "quarantine.json"))
    if err != nil {
        return Tables{}, err
    }
    if err := json.Unmarshal(qRaw, &out.Quarantine); err != nil {
        return Tables{}, err
    }
    compactRoa(&out.Roa)
    return out, nil
}

func compactRoa(doc *RoaDoc) {
    if len(doc.Entries) <= 1 {
        return
    }
    sort.Slice(doc.Entries, func(i, j int) bool {
        if doc.Entries[i].Prefix != doc.Entries[j].Prefix {
            return doc.Entries[i].Prefix < doc.Entries[j].Prefix
        }
        return doc.Entries[i].Serial < doc.Entries[j].Serial
    })
    kept := make([]RoaEntry, 0, len(doc.Entries))
    var last string
    for _, row := range doc.Entries {
        if row.Prefix == last {
            continue
        }
        kept = append(kept, row)
        last = row.Prefix
    }
    doc.Entries = kept
}
