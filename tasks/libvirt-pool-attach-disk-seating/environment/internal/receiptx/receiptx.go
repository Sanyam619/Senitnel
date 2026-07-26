package receiptx

import (
	"bufio"
	"os"
	"path/filepath"
	"strings"
)

// Receipt is a parsed cutover authorization for one domain disk.
type Receipt struct {
	OK   bool
	Pool string
	UUID string
}

// Load reads <opsDir>/receipts/<domain>-<target>.receipt as key=value. A
// receipt that is missing or not in key=value form yields OK=false.
func Load(opsDir, domain, target string) Receipt {
	p := filepath.Join(opsDir, "receipts", domain+"-"+target+".receipt")
	f, err := os.Open(p)
	if err != nil {
		return Receipt{}
	}
	defer f.Close()
	out := Receipt{}
	kv := 0
	total := 0
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		total++
		if !strings.Contains(line, "=") || strings.HasPrefix(line, "{") ||
			strings.HasPrefix(line, "\"") {
			continue
		}
		k := strings.TrimSpace(line[:strings.Index(line, "=")])
		v := strings.TrimSpace(line[strings.Index(line, "=")+1:])
		v = strings.Trim(v, "\"',")
		switch k {
		case "pool":
			out.Pool = v
			kv++
		case "uuid":
			out.UUID = v
			kv++
		}
	}
	out.OK = kv >= 2 && total > 0
	return out
}
