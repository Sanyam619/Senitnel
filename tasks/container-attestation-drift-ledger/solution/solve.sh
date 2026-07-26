#!/bin/bash
set -euo pipefail

python3 <<'PY'
from pathlib import Path

hop = Path("/app/crates/alpha/src/hop.rs")
text = hop.read_text(encoding="utf-8")
start = text.index("pub fn op_a")
end = text.index("\n}", start) + 2
replacement = '''pub fn op_a(a: &HopIn, b: &ArchSel) -> OutA {
    let root = Path::new(&b.store_root);
    if let Some(idx) = store::read_index(root, &a.store_key) {
        if idx.arch == b.arch {
            return OutA {
                value: idx.child,
            };
        }
    }
    if let Some(plat) = store::read_platform(root, &a.store_key) {
        if plat.arch == b.arch {
            return OutA {
                value: plat.digest,
            };
        }
    }
    OutA {
        value: a.dest.clone(),
    }
}'''
hop.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

subj = Path("/app/go/wire/subject.go")
subj.write_text(
    '''package wire

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
)

type attestDoc struct {
	Ref     string `json:"ref"`
	Subject string `json:"subject"`
	OK      bool   `json:"ok"`
}

type indexDoc struct {
	Digest string `json:"digest"`
	Arch   string `json:"arch"`
	Child  string `json:"child"`
}

// fold_b resolves an attestation subject string to the tracked content digest.
func fold_b(a string, b string) (string, error) {
	raw, err := os.ReadFile(a)
	if err != nil {
		return "", err
	}
	var doc attestDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return "", err
	}
	key := strings.TrimSuffix(filepath.Base(a), ".json")
	idxPath := filepath.Join(b, key, "index.json")
	idxRaw, err := os.ReadFile(idxPath)
	if err != nil {
		return doc.Subject, nil
	}
	var idx indexDoc
	if err := json.Unmarshal(idxRaw, &idx); err != nil {
		return doc.Subject, nil
	}
	if idx.Child != "" {
		return idx.Child, nil
	}
	if idx.Digest != "" && doc.Subject == idx.Digest {
		platPath := filepath.Join(b, key, "platform.json")
		platRaw, err := os.ReadFile(platPath)
		if err == nil {
			var plat indexDoc
			if json.Unmarshal(platRaw, &plat) == nil && plat.Digest != "" {
				return plat.Digest, nil
			}
		}
	}
	_ = doc.OK
	return doc.Subject, nil
}
''',
    encoding="utf-8",
)

phase = Path("/app/go/eval/phase.go")
phase.write_text(
    '''package eval

import (
	"os"
	"strconv"
	"strings"
)

// phase_c returns whether a candidate clears the active frontier check.
func phase_c(a string, b int64) (bool, error) {
	raw, err := os.ReadFile("/data/policy/roots.toml")
	if err != nil {
		return false, err
	}
	_ = a
	frontier := int64(0)
	found := false
	for _, line := range strings.Split(string(raw), "\\n") {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, "frontier_epoch") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		v := strings.TrimSpace(parts[1])
		n, err := strconv.ParseInt(v, 10, 64)
		if err != nil {
			continue
		}
		frontier = n
		found = true
	}
	if !found {
		return false, nil
	}
	if b < frontier {
		return false, nil
	}
	return true, nil
}
''',
    encoding="utf-8",
)
print("patched hop.rs subject.go phase.go")
PY

cd /app
cargo build --release --locked -p digctl
cp -f target/release/digctl /app/bin/digctl

go build -trimpath -ldflags="-s -w" -o /app/bin/provcheck ./go/cmd/provcheck
go build -trimpath -ldflags="-s -w" -o /app/bin/polgate ./go/cmd/polgate
go build -trimpath -ldflags="-s -w" -o /app/bin/replayctl ./go/cmd/replayctl

mkdir -p /output /app/var
/app/bin/replayctl
