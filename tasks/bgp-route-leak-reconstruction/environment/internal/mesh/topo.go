package mesh

import (
    "os"
    "sort"
    "strings"
)

func ListBundles(root string) ([]string, error) {
    entries, err := os.ReadDir(root)
    if err != nil {
        return nil, err
    }
    var out []string
    for _, e := range entries {
        if e.IsDir() {
            out = append(out, e.Name())
        }
    }
    sort.Strings(out)
    return out, nil
}

func NormalizeID(id string) string {
    return strings.TrimSpace(strings.ToLower(id))
}
