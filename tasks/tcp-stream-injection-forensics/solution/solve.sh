#!/usr/bin/env bash
set -euo pipefail

cd /opt/wiretap

cat > internal/k4/stitch.go <<'GOEOF'
package k4

func Stitch(buf map[int]byte, seq int, payload []byte, ts float64, preferLater bool) map[int]byte {
    if buf == nil {
        buf = make(map[int]byte)
    }
    meta := make(map[int]float64)
    for k := range buf {
        meta[k] = 0
    }
    for off := 0; off < len(payload); off++ {
        pos := seq + off
        if _, ok := buf[pos]; !ok {
            buf[pos] = payload[off]
            meta[pos] = ts
            continue
        }
        if preferLater {
            if ts >= meta[pos] {
                buf[pos] = payload[off]
                meta[pos] = ts
            }
        } else if ts < meta[pos] || meta[pos] == 0 {
            buf[pos] = payload[off]
            meta[pos] = ts
        }
    }
    return buf
}
GOEOF

cat > internal/m2/queue.go <<'GOEOF'
package m2

func Drain(buf map[int]byte, start int) ([]byte, int) {
    out := make([]byte, 0)
    pos := start
    for {
        b, ok := buf[pos]
        if !ok {
            break
        }
        out = append(out, b)
        pos++
    }
    return out, pos
}
GOEOF

cat > internal/p7/limit.go <<'GOEOF'
package p7

func Ceiling(rcvNxt int, win int, seq int, length int) bool {
    end := seq + length
    return end <= rcvNxt+win
}
GOEOF

cat > internal/n5/challenge.go <<'GOEOF'
package n5

func Compare(a []byte, b []byte) (same bool, ranges [][2]int) {
    n := len(a)
    if len(b) < n {
        n = len(b)
    }
    same = len(a) == len(b)
    for i := 0; i < n; i++ {
        if a[i] != b[i] {
            same = false
            ranges = append(ranges, [2]int{i, i + 1})
        }
    }
    if len(a) != len(b) {
        same = false
    }
    return same, ranges
}
GOEOF

cat > internal/r8/emit.go <<'GOEOF'
package r8

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "lab.wiretap/app/internal/m2"
    "lab.wiretap/app/internal/n5"
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
    Version int            `json:"version"`
    Flows   map[string]row   `json:"flows"`
}

type span struct {
    seq int
    payload []byte
    ts float64
}

func relOff(abs int, base int) int { return abs - base }

func assemble(segs []span, base int, preferLater bool, rejectLater bool, win int, shrinkTs float64, shrinkWin int) ([]byte, [][2]int, []note) {
    sort.Slice(segs, func(i, j int) bool {
        if segs[i].ts == segs[j].ts {
            return segs[i].seq < segs[j].seq
        }
        return segs[i].ts < segs[j].ts
    })
    buf := map[int]byte{}
    meta := map[int]float64{}
    seen := map[[2]int][]byte{}
    injected := [][2]int{}
    notes := []note{}
    rcv := base
    if len(segs) > 0 {
        rcv = segs[0].seq
    }
    activeWin := win
    for _, seg := range segs {
        if shrinkTs > 0 && seg.ts >= shrinkTs {
            activeWin = shrinkWin
        }
        if !p7.Ceiling(rcv, activeWin, seg.seq, len(seg.payload)) {
            continue
        }
        key := [2]int{seg.seq, seg.seq + len(seg.payload)}
        if prior, ok := seen[key]; ok {
            same, ranges := n5.Compare(prior, seg.payload)
            if !same {
                for _, rg := range ranges {
                    injected = append(injected, [2]int{relOff(seg.seq+rg[0], base), relOff(seg.seq+rg[1], base)})
                }
                if rejectLater {
                    continue
                }
            }
        } else {
            seen[key] = append([]byte(nil), seg.payload...)
        }
        for off := 0; off < len(seg.payload); off++ {
            pos := seg.seq + off
            if _, ok := buf[pos]; ok {
                kept := "later"
                if !preferLater && seg.ts < meta[pos] {
                    kept = "earlier"
                }
                notes = append(notes, note{RelOff: relOff(pos, base), Dir: "", Kept: kept})
            }
            if preferLater {
                if old, ok := meta[pos]; !ok || seg.ts >= old {
                    buf[pos] = seg.payload[off]
                    meta[pos] = seg.ts
                }
            } else if old, ok := meta[pos]; !ok || seg.ts < old || old == 0 {
                buf[pos] = seg.payload[off]
                meta[pos] = seg.ts
            }
        }
        end := seg.seq + len(seg.payload)
        if end > rcv {
            rcv = end
        }
    }
    out, _ := m2.Drain(buf, base)
    return out, injected, notes
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
        shrinkTs := 0.0
        shrinkWin := 65535
        if f.WindowShrinkTS != nil {
            shrinkTs = *f.WindowShrinkTS
        }
        if f.WindowShrinkBytes != nil {
            shrinkWin = *f.WindowShrinkBytes
        }
        cOut, cInj, cNotes := assemble(c2s, cBase, true, true, 65535, shrinkTs, shrinkWin)
        sOut, sInj, sNotes := assemble(s2c, sBase, true, false, 65535, 0, 65535)
        for i := range cNotes {
            cNotes[i].Dir = "c2s"
        }
        for i := range sNotes {
            sNotes[i].Dir = "s2c"
        }
        if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_c2s.bin"), cOut, 0o644); err != nil {
            return err
        }
        if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_s2c.bin"), sOut, 0o644); err != nil {
            return err
        }
        flows[f.ID] = row{
            C2SLen: len(cOut), S2CLen: len(sOut),
            C2SInjected: cInj, S2CInjected: sInj,
            Overlap: append(cNotes, sNotes...),
        }
    }
    payload := doc{Version: 1, Flows: flows}
    raw, err := json.MarshalIndent(payload, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(filepath.Join(outDir, "findings.json"), raw, 0o644)
}
GOEOF

python3 -c "from pathlib import Path; path=Path('internal/r8/inject.go'); text=path.read_text(encoding='utf-8'); old='for si, seg := range ordered {\n        skipNotes := false\n        for _, prior := range ordered[:si] {\n            if prior.Seq == seg.Seq && prior.Ts < seg.Ts && bytes.Equal(prior.Payload, seg.Payload) {\n                skipNotes = true\n                break\n            }\n        }\n        for off := 0; off < len(seg.Payload); off++ {\n            pos := seg.Seq + off\n            if _, ok := buf[pos]; ok && !skipNotes {'; new='for _, seg := range ordered {\n        for off := 0; off < len(seg.Payload); off++ {\n            pos := seg.Seq + off\n            if _, ok := buf[pos]; ok {'; assert old in text, 'inject.go overlap skip anchor missing'; text=text.replace(old, new, 1); text=text.replace('    '+chr(34)+'bytes'+chr(34)+'\n', '', 1); path.write_text(text, encoding='utf-8')"

go build -o /opt/wiretap/bin/wiretap ./cmd/wiretap
rm -rf /output
mkdir -p /output
/opt/wiretap/bin/wiretap analyze --manifest /opt/wiretap/data/manifest.json --out /output
