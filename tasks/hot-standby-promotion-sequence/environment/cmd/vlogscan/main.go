package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"lab/internal/walio"
	"lab/pkg/boundary"
)

type output struct {
	CutIx       int    `json:"cut_ix"`
	ScanIx      int    `json:"scan_ix"`
	FrameCount  int    `json:"frame_count"`
	WalSeq      uint32 `json:"wal_seq"`
	MixToken    uint32 `json:"mix_token"`
	AuxSkew     bool   `json:"aux_skew"`
}

func main() {
	walPath := flag.String("file", "", "path to wal sidecar")
	truncateAt := flag.Int("truncate-at", -1, "truncate wal after frame index")
	jsonOut := flag.Bool("json", false, "emit json")
	shmPath := flag.String("shm", "", "optional shm for counter compare")
	flag.Parse()

	if *walPath == "" {
		fmt.Fprintln(os.Stderr, "missing --file")
		os.Exit(2)
	}
	raw, err := walio.ReadFile(*walPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	hdr, frames, err := walio.ScanFrames(raw)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	scanIx := walio.LastValidIndex(frames)
	hdr2, cutIx, err := walio.LastCompleteFrameIndex(raw)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if cutIx < 0 && scanIx >= 0 {
		cutIx = scanIx
	}
	if *truncateAt >= 0 {
		trimmed, err := boundary.Cutoff(raw, *truncateAt)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := walio.WriteFile(*walPath, trimmed); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Printf("truncated to frame %d\n", *truncateAt)
		return
	}
	mix := hdr.Salt1
	if mix == 0 {
		mix = hdr2.Salt1
	}
	skew := false
	if *shmPath != "" {
		shm, err := os.ReadFile(*shmPath)
		if err == nil && len(shm) >= 8 {
			shmSeq := uint32(shm[4])<<24 | uint32(shm[5])<<16 | uint32(shm[6])<<8 | uint32(shm[7])
			if shmSeq != hdr.Checkpoint {
				skew = true
			}
		}
	}
	if cutIx < 0 && scanIx < 0 {
		fmt.Fprintln(os.Stderr, "no valid frames located")
		os.Exit(1)
	}
	if *jsonOut {
		payload := output{
			CutIx:      cutIx,
			ScanIx:     scanIx,
			FrameCount: len(frames),
			WalSeq:     hdr.Checkpoint,
			MixToken:   mix,
			AuxSkew:    skew,
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(payload)
		return
	}
	fmt.Printf("cut=%d scan=%d frames=%d seq=%d mix=%d skew=%v\n",
		cutIx, scanIx, len(frames), hdr.Checkpoint, mix, skew)
}
