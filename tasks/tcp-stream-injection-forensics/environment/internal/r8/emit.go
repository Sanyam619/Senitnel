package r8

import (
    "encoding/json"
    "os"
    "path/filepath"
    "lab.wiretap/app/internal/k4"
    "lab.wiretap/app/internal/m2"
    "lab.wiretap/app/internal/p7"
    "lab.wiretap/app/internal/scan"
    "lab.wiretap/app/pkg/lane"
)

type note struct {
    RelOff int    `json:"rel_off"`
    Dir    string `json:"dir"`
    Kept   string `json:"kept"`
}

type row struct {
    C2SLen      int      `json:"c2s_len"`
    S2CLen      int      `json:"s2c_len"`
    C2SInjected [][2]int `json:"c2s_injected"`
    S2CInjected [][2]int `json:"s2c_injected"`
    Overlap     []note   `json:"overlap_notes"`
}

type doc struct {
    Version int          `json:"version"`
    Flows   map[string]row `json:"flows"`
}

type span struct {
    seq     int
    payload []byte
    ts      float64
}

func laneSegs(segs []span) []LaneSeg {
    out := make([]LaneSeg, len(segs))
    for i, s := range segs {
        out[i] = LaneSeg{Seq: s.seq, Payload: s.payload}
    }
    return out
}

func southSegs(segs []span) []k4.SouthSeg {
    out := make([]k4.SouthSeg, len(segs))
    for i, s := range segs {
        out[i] = k4.SouthSeg{Seq: s.seq, Payload: s.payload, Ts: s.ts}
    }
    return out
}

func Analyze(manifestPath, outDir string) error {
    mf, err := lane.LoadManifest(manifestPath)
    if err != nil {
        return err
    }
    if err := os.MkdirAll(filepath.Join(outDir, "reassembled"), 0o755); err != nil {
        return err
    }
    flows := map[string]row{}
    for _, f := range mf.Flows {
        pkts, err := scan.ReadFile(f.Capture)
        if err != nil {
            return err
        }
        c2s := []span{}
        s2c := []span{}
        cBase := f.ISNClient + 1
        sBase := f.ISNServer + 1
        for _, p := range pkts {
            if p.PayloadLen == 0 {
                continue
            }
            if p.Src == f.Client && p.Dst == f.Server && int(p.Sport) == f.ClientPort && int(p.Dport) == f.ServerPort {
                c2s = append(c2s, span{seq: p.Seq, payload: append([]byte(nil), p.Payload...), ts: p.Ts})
            }
            if p.Src == f.Server && p.Dst == f.Client && int(p.Sport) == f.ServerPort && int(p.Dport) == f.ClientPort {
                s2c = append(s2c, span{seq: p.Seq, payload: append([]byte(nil), p.Payload...), ts: p.Ts})
            }
        }
        cBuf := k4.SouthMerge(southSegs(c2s))
        sBuf := map[int]byte{}
        for _, s := range s2c {
            sBuf = k4.Stitch(sBuf, s.seq, s.payload, s.ts, true)
        }
        cOut, _ := m2.Drain(cBuf, cBase)
        sOut, _ := m2.Drain(sBuf, sBase)
        cInj := ContestedOffsets(laneSegs(c2s), cBase)
        sInj := ContestedOffsets(laneSegs(s2c), sBase)
        cTimed := make([]timedLaneSeg, len(c2s))
        for i, s := range c2s {
            cTimed[i] = timedLaneSeg{Seq: s.seq, Payload: append([]byte(nil), s.payload...), Ts: s.ts}
        }
        sTimed := make([]timedLaneSeg, len(s2c))
        for i, s := range s2c {
            sTimed[i] = timedLaneSeg{Seq: s.seq, Payload: append([]byte(nil), s.payload...), Ts: s.ts}
        }
        overlap := append(
            LaneOverlapNotes(cTimed, cBase, "c2s", true),
            LaneOverlapNotes(sTimed, sBase, "s2c", true)...,
        )
        _ = p7.Ceiling(0, 0, 0, 0)
        if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_c2s.bin"), cOut, 0o644); err != nil {
            return err
        }
        if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_s2c.bin"), sOut, 0o644); err != nil {
            return err
        }
        flows[f.ID] = row{
            C2SLen: len(cOut) + 1, S2CLen: len(sOut) + 1,
            C2SInjected: cInj, S2CInjected: sInj,
            Overlap: overlap,
        }
    }
    payload := doc{Version: 1, Flows: flows}
    raw, err := json.MarshalIndent(payload, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(filepath.Join(outDir, "findings.json"), raw, 0o644)
}
