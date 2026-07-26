package ingest

type Route struct {
    Prefix    string `json:"prefix"`
    NextHop   string `json:"next_hop"`
    ASPath    []int  `json:"as_path"`
    LocalPref int    `json:"local_pref"`
    MED       int    `json:"med"`
    Origin    string `json:"origin"`
}

type RibFile struct {
    Peer   string  `json:"peer"`
    Routes []Route `json:"routes"`
}

type PeerMeta struct {
    Name string `json:"name"`
    Rib  string `json:"rib"`
    AS   int    `json:"as"`
    Addr string `json:"addr"`
}

type Manifest struct {
    ID    string     `json:"id"`
    Peers []PeerMeta `json:"peers"`
}
