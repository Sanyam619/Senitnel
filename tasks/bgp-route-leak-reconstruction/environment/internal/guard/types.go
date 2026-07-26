package guard

type RoaEntry struct {
    Prefix    string `json:"prefix"`
    MaxLength int    `json:"max_length"`
    OriginASN int    `json:"origin_asn"`
    Serial    int    `json:"serial"`
    State     string `json:"state"`
}

type RoaDoc struct {
    Entries []RoaEntry `json:"entries"`
}

type HoldEntry struct {
    Prefix string `json:"prefix"`
    Peer   string `json:"peer"`
    Reason string `json:"reason"`
}

type QuarantineDoc struct {
    Holds []HoldEntry `json:"holds"`
}

type Tables struct {
    Roa         RoaDoc
    Quarantine  QuarantineDoc
}
