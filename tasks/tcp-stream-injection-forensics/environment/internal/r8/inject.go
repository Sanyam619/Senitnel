package r8

import (
    "bytes"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "lab.wiretap/app/internal/scan"
    "lab.wiretap/app/pkg/lane"
)

type LaneSeg struct {
    Seq     int
    Payload []byte
}

type timedLaneSeg struct {
    Seq     int
    Payload []byte
    Ts      float64
}

type contestedRow struct {
    C2SLen      int      `json:"c2s_len"`
    S2CLen      int      `json:"s2c_len"`
    C2SInjected [][2]int `json:"c2s_injected"`
    S2CInjected [][2]int `json:"s2c_injected"`
    Overlap     []note   `json:"overlap_notes"`
}

type contestedDoc struct {
    Version int                     `json:"version"`
    Flows   map[string]contestedRow `json:"flows"`
}

func disagreeRanges(a, b []byte) [][2]int {
    n := len(a)
    if len(b) < n {
        n = len(b)
    }
    out := [][2]int{}
    for i := 0; i < n; i++ {
        if a[i] != b[i] {
            out = append(out, [2]int{i, i + 1})
        }
    }
    return out
}

func ContestedOffsets(segs []LaneSeg, base int) [][2]int {
    seen := map[[2]int][]byte{}
    injected := [][2]int{}
    for _, s := range segs {
        if len(s.Payload) == 0 {
            continue
        }
        key := [2]int{s.Seq, s.Seq + len(s.Payload)}
        if prior, ok := seen[key]; ok {
            for _, rg := range disagreeRanges(prior, s.Payload) {
                injected = append(injected, [2]int{s.Seq + rg[0] - base, s.Seq + rg[1] - base})
            }
        } else {
            seen[key] = append([]byte(nil), s.Payload...)
        }
    }
    return injected
}

func LaneOverlapNotes(segs []timedLaneSeg, base int, dir string, preferLater bool) []note {
    if len(segs) == 0 {
        return nil
    }
    ordered := append([]timedLaneSeg(nil), segs...)
    sort.Slice(ordered, func(i, j int) bool {
        if ordered[i].Ts == ordered[j].Ts {
            return ordered[i].Seq < ordered[j].Seq
        }
        return ordered[i].Ts < ordered[j].Ts
    })
    buf := map[int]byte{}
    meta := map[int]float64{}
    notes := []note{}
    for si, seg := range ordered {
        skipNotes := false
        for _, prior := range ordered[:si] {
            if prior.Seq == seg.Seq && prior.Ts < seg.Ts && bytes.Equal(prior.Payload, seg.Payload) {
                skipNotes = true
                break
            }
        }
        for off := 0; off < len(seg.Payload); off++ {
            pos := seg.Seq + off
            if _, ok := buf[pos]; ok && !skipNotes {
                kept := "later"
                if !preferLater {
                    kept = "earlier"
                }
                notes = append(notes, note{RelOff: pos - base, Dir: dir, Kept: kept})
            }
            if preferLater {
                if old, ok := meta[pos]; !ok || seg.Ts >= old {
                    buf[pos] = seg.Payload[off]
                    meta[pos] = seg.Ts
                }
            } else if old, ok := meta[pos]; !ok || seg.Ts < old || old == 0 {
                buf[pos] = seg.Payload[off]
                meta[pos] = seg.Ts
            }
        }
    }
    return notes
}

func flowTimedLaneSegs(f lane.Flow) (c2s []timedLaneSeg, s2c []timedLaneSeg, cBase int, sBase int, err error) {
    pkts, err := scan.ReadFile(f.Capture)
    if err != nil {
        return nil, nil, 0, 0, err
    }
    cBase = f.ISNClient + 1
    sBase = f.ISNServer + 1
    for _, p := range pkts {
        if p.PayloadLen == 0 {
            continue
        }
        if p.Src == f.Client && p.Dst == f.Server && int(p.Sport) == f.ClientPort && int(p.Dport) == f.ServerPort {
            c2s = append(c2s, timedLaneSeg{Seq: p.Seq, Payload: append([]byte(nil), p.Payload...), Ts: p.Ts})
        }
        if p.Src == f.Server && p.Dst == f.Client && int(p.Sport) == f.ServerPort && int(p.Dport) == f.ClientPort {
            s2c = append(s2c, timedLaneSeg{Seq: p.Seq, Payload: append([]byte(nil), p.Payload...), Ts: p.Ts})
        }
    }
    return c2s, s2c, cBase, sBase, nil
}

func flowLaneSegs(f lane.Flow) (c2s []LaneSeg, s2c []LaneSeg, cBase int, sBase int, err error) {
    cTimed, sTimed, cBase, sBase, err := flowTimedLaneSegs(f)
    if err != nil {
        return nil, nil, 0, 0, err
    }
    for _, s := range cTimed {
        c2s = append(c2s, LaneSeg{Seq: s.Seq, Payload: s.Payload})
    }
    for _, s := range sTimed {
        s2c = append(s2c, LaneSeg{Seq: s.Seq, Payload: s.Payload})
    }
    return c2s, s2c, cBase, sBase, nil
}

func AttachContested(manifestPath, outDir string) error {
    findingsPath := filepath.Join(outDir, "findings.json")
    raw, err := os.ReadFile(findingsPath)
    if err != nil {
        return err
    }
    var payload contestedDoc
    if err := json.Unmarshal(raw, &payload); err != nil {
        return err
    }
    mf, err := lane.LoadManifest(manifestPath)
    if err != nil {
        return err
    }
    for _, f := range mf.Flows {
        c2s, s2c, cBase, sBase, err := flowTimedLaneSegs(f)
        if err != nil {
            return err
        }
        row, ok := payload.Flows[f.ID]
        if !ok {
            row = contestedRow{}
        }
        plainC2S := make([]LaneSeg, len(c2s))
        plainS2C := make([]LaneSeg, len(s2c))
        for i, s := range c2s {
            plainC2S[i] = LaneSeg{Seq: s.Seq, Payload: s.Payload}
        }
        for i, s := range s2c {
            plainS2C[i] = LaneSeg{Seq: s.Seq, Payload: s.Payload}
        }
        row.C2SInjected = ContestedOffsets(plainC2S, cBase)
        row.S2CInjected = ContestedOffsets(plainS2C, sBase)
        row.Overlap = append(
            LaneOverlapNotes(c2s, cBase, "c2s", true),
            LaneOverlapNotes(s2c, sBase, "s2c", true)...,
        )
        payload.Flows[f.ID] = row
    }
    out, err := json.MarshalIndent(payload, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(findingsPath, out, 0o644)
}
