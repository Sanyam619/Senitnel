package seatx

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"

	"libvirt.lab/virtattach/internal/planx"
)

var nameRe = regexp.MustCompile(`(?s)<name>\s*([^<]+?)\s*</name>`)
var uuidRe = regexp.MustCompile(`<uuid>\s*([^<]+?)\s*</uuid>`)
var pathRe = regexp.MustCompile(`(?s)<target>.*?<path>\s*([^<]+?)\s*</path>`)

// IndexDefs scans the domain definition directory and maps each domain name to
// the file that defines it.
func IndexDefs(dir string) (map[string]string, error) {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	out := map[string]string{}
	for _, e := range ents {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".xml") {
			continue
		}
		p := filepath.Join(dir, e.Name())
		b, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		if !strings.Contains(string(b), "<domain") {
			continue
		}
		m := nameRe.FindStringSubmatch(string(b))
		if m != nil {
			out[strings.TrimSpace(m[1])] = p
		}
	}
	return out, nil
}

// SurfaceIdentity reads the pool definition file and returns its declared
// identity (uuid and target path).
func SurfaceIdentity(storageDir, pool string) (planx.Ident, error) {
	p := filepath.Join(storageDir, "pool_"+pool+".xml")
	b, err := os.ReadFile(p)
	if err != nil {
		return planx.Ident{}, err
	}
	s := string(b)
	id := planx.Ident{}
	if m := uuidRe.FindStringSubmatch(s); m != nil {
		id.UUID = strings.TrimSpace(m[1])
	}
	if m := pathRe.FindStringSubmatch(s); m != nil {
		id.Path = strings.TrimSpace(m[1])
	}
	return id, nil
}

// State is the parsed runtime state of a pool.
type State struct {
	State string
	Path  string
}

// PoolState reads <root>/<pool>/pool.state as key=value.
func PoolState(root, pool string) State {
	p := filepath.Join(root, pool, "pool.state")
	f, err := os.Open(p)
	if err != nil {
		return State{}
	}
	defer f.Close()
	out := State{}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if strings.HasPrefix(line, "state=") {
			out.State = strings.TrimSpace(strings.TrimPrefix(line, "state="))
		} else if strings.HasPrefix(line, "path=") {
			out.Path = strings.TrimSpace(strings.TrimPrefix(line, "path="))
		}
	}
	return out
}

// Guard takes an exclusive lock on a per-request marker and returns a release
// that removes the transient marker and unlocks.
func Guard(leaseDir, key string) (func() error, error) {
	if err := os.MkdirAll(leaseDir, 0o755); err != nil {
		return nil, err
	}
	lock := filepath.Join(leaseDir, key+".lock")
	f, err := os.OpenFile(lock, os.O_CREATE|os.O_RDWR, 0o644)
	if err != nil {
		return nil, err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX); err != nil {
		_ = f.Close()
		return nil, fmt.Errorf("flock: %w", err)
	}
	part := filepath.Join(leaseDir, key+".part")
	if err := os.WriteFile(part, []byte("1\n"), 0o644); err != nil {
		_ = syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
		_ = f.Close()
		return nil, err
	}
	return func() error {
		_ = os.Remove(part)
		_ = os.Remove(lock)
		_ = syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
		return f.Close()
	}, nil
}
