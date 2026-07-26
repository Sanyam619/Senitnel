package r8

// OverlapNote records duplicate-arrival resolution, including identical full-span replays.
type OverlapNote struct {
    RelOff int    `json:"rel_off"`
    Dir    string `json:"dir"`
    Kept   string `json:"kept"`
}

// VerifyContractRow documents reconciled lane metadata checked by external verification.
type VerifyContractRow struct {
    C2SLen      int           `json:"c2s_len"`
    S2CLen      int           `json:"s2c_len"`
    C2SInjected [][2]int      `json:"c2s_injected"`
    S2CInjected [][2]int      `json:"s2c_injected"`
    OverlapNotes []OverlapNote `json:"overlap_notes"`
}
