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
	LastValidIndex int    `json:"last_valid_index"`
	FrameCount     int    `json:"frame_count"`
	WalCheckpoint  uint32 `json:"wal_checkpoint"`
	Salt           uint32 `json:"salt"`
	ShmMismatch    bool   `json:"shm_counter_mismatch"`
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
	last := walio.LastValidIndex(frames)
	hdr2, fallback, err := walio.LastCompleteFrameIndex(raw, 128)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if last < 0 {
		last = fallback
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
	salt := hdr.Salt1
	if salt == 0 {
		salt = hdr2.Salt1
	}
	mismatch := false
	if *shmPath != "" {
		shm, err := os.ReadFile(*shmPath)
		if err == nil && len(shm) >= 8 {
			shmSeq := uint32(shm[4])<<24 | uint32(shm[5])<<16 | uint32(shm[6])<<8 | uint32(shm[7])
			if shmSeq != hdr.Checkpoint {
				mismatch = true
			}
		}
	}
	if last < 0 {
		fmt.Fprintln(os.Stderr, "no valid frames located")
		os.Exit(1)
	}
	if *jsonOut {
		payload := output{
			LastValidIndex: last,
			FrameCount:     len(frames),
			WalCheckpoint:  hdr.Checkpoint,
			Salt:           salt,
			ShmMismatch:    mismatch,
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(payload)
		return
	}
	fmt.Printf("valid_through=%d frames=%d checkpoint=%d salt=%d mismatch=%v\n",
		last, len(frames), hdr.Checkpoint, salt, mismatch)
}
