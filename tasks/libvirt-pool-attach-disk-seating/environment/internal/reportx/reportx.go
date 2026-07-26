package reportx

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type poolEntry struct {
	Name  string `json:"name"`
	Path  string `json:"path"`
	UUID  string `json:"uuid"`
	State string `json:"state"`
}

type diskEntry struct {
	Domain   string `json:"domain"`
	Target   string `json:"target"`
	Source   string `json:"source"`
	Pool     string `json:"pool"`
	Attached bool   `json:"attached"`
}

// Report is the reconciled attach report.
type Report struct {
	SchemaTag string      `json:"schema_tag"`
	Pools     []poolEntry `json:"pools"`
	Disks     []diskEntry `json:"disks"`
	AttachOKV bool        `json:"attach_ok"`
}

// New returns an empty report with the fixed schema tag.
func New() *Report {
	return &Report{SchemaTag: "libvirt-attach-v1", Pools: []poolEntry{}, Disks: []diskEntry{}}
}

// AddPool appends a pool entry.
func (r *Report) AddPool(name, path, uuid, state string) {
	r.Pools = append(r.Pools, poolEntry{Name: name, Path: path, UUID: uuid, State: state})
}

// AddDisk appends a disk entry.
func (r *Report) AddDisk(domain, target, source, pool string, attached bool) {
	r.Disks = append(r.Disks, diskEntry{
		Domain: domain, Target: target, Source: source, Pool: pool, Attached: attached,
	})
}

// AttachOK reports whether every disk attached; it also finalizes the field.
func (r *Report) AttachOK() bool {
	all := len(r.Disks) > 0
	for _, d := range r.Disks {
		if !d.Attached {
			all = false
		}
	}
	r.AttachOKV = all
	return all
}

// Write serializes the report deterministically.
func Write(path string, r *Report) error {
	r.AttachOK()
	b, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0o644)
}
