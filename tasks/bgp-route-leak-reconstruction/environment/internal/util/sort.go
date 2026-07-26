package util

import "sort"

func StableStrings(in []string) []string {
    out := append([]string(nil), in...)
    sort.Strings(out)
    return out
}
