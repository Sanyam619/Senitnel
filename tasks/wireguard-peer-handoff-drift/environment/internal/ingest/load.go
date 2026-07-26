package ingest

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
)

type Member struct {
    ID         string   `json:"id"`
    Pubkey     string   `json:"pubkey"`
    Endpoint   string   `json:"endpoint"`
    AllowedIPs []string `json:"allowed_ips"`
}

type EpochRow struct {
    Epoch   int      `json:"epoch"`
    Members []Member `json:"members"`
}

type EpochTable struct {
    CurrentEpoch int        `json:"current_epoch"`
    Epochs       []EpochRow `json:"epochs"`
}

type LiveState struct {
    Epoch      int      `json:"epoch"`
    MemberIDs  []string `json:"member_ids"`
    RetiredIDs []string `json:"retired_ids"`
}

type Manifest struct {
    NodeID      string `json:"node_id"`
    TargetEpoch int    `json:"target_epoch"`
}

type Pending struct {
    Epoch     int      `json:"epoch"`
    MemberIDs []string `json:"member_ids"`
}

type Bundle struct {
    Dir     string
    Manifest Manifest
    Table   EpochTable
    Live    LiveState
    Pending Pending
}

func LoadBundle(dir string) (Bundle, error) {
    var b Bundle
    b.Dir = dir
    if err := readJSON(filepath.Join(dir, "manifest.json"), &b.Manifest); err != nil {
        return b, err
    }
    if err := readJSON(filepath.Join(dir, "epoch_table.json"), &b.Table); err != nil {
        return b, err
    }
    if err := readJSON(filepath.Join(dir, "live_state.json"), &b.Live); err != nil {
        return b, err
    }
    if err := readJSON(filepath.Join(dir, "pending.json"), &b.Pending); err != nil {
        return b, err
    }
    return b, nil
}

func ListBundles(root string) ([]Bundle, error) {
    entries, err := os.ReadDir(root)
    if err != nil {
        return nil, err
    }
    names := make([]string, 0, len(entries))
    for _, e := range entries {
        if e.IsDir() {
            names = append(names, e.Name())
        }
    }
    sort.Strings(names)
    out := make([]Bundle, 0, len(names))
    for _, name := range names {
        b, err := LoadBundle(filepath.Join(root, name))
        if err != nil {
            return nil, err
        }
        out = append(out, b)
    }
    return out, nil
}

func readJSON(path string, v any) error {
    raw, err := os.ReadFile(path)
    if err != nil {
        return err
    }
    return json.Unmarshal(raw, v)
}

func (b Bundle) RowForEpoch(ep int) []Member {
    for _, row := range b.Table.Epochs {
        if row.Epoch == ep {
            return row.Members
        }
    }
    return nil
}

func MemberIDs(ms []Member) []string {
    ids := make([]string, 0, len(ms))
    for _, m := range ms {
        ids = append(ids, m.ID)
    }
    sort.Strings(ids)
    return ids
}
