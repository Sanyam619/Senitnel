package lane

import (
    "encoding/json"
    "os"
)

type Flow struct {
    ID                 string   `json:"id"`
    Capture            string   `json:"capture"`
    Client             string   `json:"client"`
    Server             string   `json:"server"`
    ClientPort         int      `json:"client_port"`
    ServerPort         int      `json:"server_port"`
    ISNClient          int      `json:"isn_client"`
    ISNServer          int      `json:"isn_server"`
    WindowShrinkTS     *float64 `json:"window_shrink_ts"`
    // WindowShrinkBytes is receive-window size beyond rcv_nxt after WindowShrinkTS.
    WindowShrinkBytes  *int     `json:"window_shrink_bytes"`
}

type Manifest struct {
    Version int    `json:"version"`
    Flows   []Flow `json:"flows"`
}

func LoadManifest(path string) (*Manifest, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var mf Manifest
    if err := json.Unmarshal(raw, &mf); err != nil {
        return nil, err
    }
    return &mf, nil
}
