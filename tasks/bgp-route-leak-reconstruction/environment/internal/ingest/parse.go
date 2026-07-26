package ingest

import (
    "encoding/json"
    "os"
    "sort"
)

type LoadedRoute struct {
    Scenario string
    Peer     string
    PeerAS   int
    PeerAddr string
    Route
}

func LoadManifest(path string) (Manifest, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return Manifest{}, err
    }
    var m Manifest
    if err := json.Unmarshal(raw, &m); err != nil {
        return Manifest{}, err
    }
    sort.Slice(m.Peers, func(i, j int) bool { return m.Peers[i].Name < m.Peers[j].Name })
    return m, nil
}

func LoadRib(base, rel string) (RibFile, error) {
    raw, err := os.ReadFile(base + "/" + rel)
    if err != nil {
        return RibFile{}, err
    }
    var r RibFile
    if err := json.Unmarshal(raw, &r); err != nil {
        return RibFile{}, err
    }
    sort.Slice(r.Routes, func(i, j int) bool { return r.Routes[i].Prefix < r.Routes[j].Prefix })
    return r, nil
}

func LoadScenario(dir string) ([]LoadedRoute, error) {
    m, err := LoadManifest(dir + "/manifest.json")
    if err != nil {
        return nil, err
    }
    var out []LoadedRoute
    for _, p := range m.Peers {
        rib, err := LoadRib(dir, p.Rib)
        if err != nil {
            return nil, err
        }
        for _, rt := range rib.Routes {
            out = append(out, LoadedRoute{
                Scenario: m.ID,
                Peer:     p.Name,
                PeerAS:   p.AS,
                PeerAddr: p.Addr,
                Route:    rt,
            })
        }
    }
    sort.Slice(out, func(i, j int) bool {
        if out[i].Prefix != out[j].Prefix {
            return out[i].Prefix < out[j].Prefix
        }
        return out[i].Peer < out[j].Peer
    })
    return out, nil
}
