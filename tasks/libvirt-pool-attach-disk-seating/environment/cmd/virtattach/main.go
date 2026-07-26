package main

import (
	"fmt"
	"os"
	"path/filepath"

	"libvirt.lab/virtattach/internal/planx"
	"libvirt.lab/virtattach/internal/receiptx"
	"libvirt.lab/virtattach/internal/reportx"
	"libvirt.lab/virtattach/internal/seatx"
)

func env(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func main() {
	qemuDir := env("QEMU_DIR", "/etc/libvirt/qemu")
	storageDir := env("STORAGE_DIR", "/etc/libvirt/storage")
	opsDir := env("OPS_DIR", "/var/lib/libvirt/ops")
	stateRoot := env("POOL_STATE_ROOT", "/var/lib/libvirt/storage")
	roster := env("SEAT_ROSTER", filepath.Join(qemuDir, "seat.roster"))
	planPath := env("SEAT_PLAN", filepath.Join(opsDir, "seating.plan"))
	attachD := env("ATTACH_D", filepath.Join(qemuDir, "attach.d"))
	leaseDir := env("LEASE_DIR", "/var/run/libvirt")
	report := env("ATTACH_REPORT", "/output/libvirt-attach.json")

	rows, err := planx.RosterRows(roster)
	if err != nil {
		fmt.Fprintf(os.Stderr, "roster: %v\n", err)
		os.Exit(1)
	}
	plan, err := planx.PlanMap(planPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "plan: %v\n", err)
		os.Exit(1)
	}
	mode := planx.SelectMode(attachD)

	xmlIndex, err := seatx.IndexDefs(qemuDir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "defs: %v\n", err)
		os.Exit(1)
	}

	if err := os.MkdirAll(leaseDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "lease: %v\n", err)
		os.Exit(1)
	}

	rep := reportx.New()
	poolSeen := map[string]bool{}

	for _, r := range rows {
		rel, err := seatx.Guard(leaseDir, r.Domain+"-"+r.Target)
		if err != nil {
			fmt.Fprintf(os.Stderr, "guard: %v\n", err)
			os.Exit(1)
		}

		surf, err := seatx.SurfaceIdentity(storageDir, r.Pool)
		if err != nil {
			_ = rel()
			fmt.Fprintf(os.Stderr, "surface %s: %v\n", r.Pool, err)
			os.Exit(1)
		}
		dur := plan[r.Pool]

		chosen := surf
		if mode == "durable" {
			chosen = dur
		}

		if defPath, ok := xmlIndex[r.Domain]; ok {
			if err := seatx.Rebind(defPath, r.Target, chosen.UUID); err != nil {
				_ = rel()
				fmt.Fprintf(os.Stderr, "rebind %s: %v\n", r.Domain, err)
				os.Exit(1)
			}
		}

		st := seatx.PoolState(stateRoot, r.Pool)
		stateActive := st.State == "active"

		rc := receiptx.Load(opsDir, r.Domain, r.Target)
		receiptOK := rc.OK && rc.Pool == r.Pool && rc.UUID == dur.UUID && dur.UUID != ""

		attached := mode == "durable" && chosen.UUID == dur.UUID && dur.UUID != "" &&
			stateActive && receiptOK

		if !poolSeen[r.Pool] {
			poolSeen[r.Pool] = true
			state := "inactive"
			if stateActive {
				state = "active"
			}
			rep.AddPool(r.Pool, chosen.Path, chosen.UUID, state)
		}

		src := ""
		if chosen.Path != "" {
			src = filepath.Join(chosen.Path, r.Volume)
		}
		rep.AddDisk(r.Domain, r.Target, src, r.Pool, attached)

		if err := rel(); err != nil {
			fmt.Fprintf(os.Stderr, "release: %v\n", err)
			os.Exit(1)
		}
	}

	if err := reportx.Write(report, rep); err != nil {
		fmt.Fprintf(os.Stderr, "report: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("done disks=%d ok=%v\n", len(rows), rep.AttachOK())
}
