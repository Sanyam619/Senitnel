package chip

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
)

type StateFile struct {
	Replayed bool              `json:"replayed"`
	Regs     map[int][]byte      `json:"-"`
	RegHex   map[string]string   `json:"regs"`
}

func LoadState(path string) (*StateFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var sf StateFile
	if err := json.Unmarshal(raw, &sf); err != nil {
		return nil, err
	}
	sf.Regs = make(map[int][]byte)
	for k, v := range sf.RegHex {
		var bank int
		if _, err := fmt.Sscanf(k, "%d", &bank); err != nil {
			continue
		}
		b, err := hex.DecodeString(v)
		if err != nil {
			return nil, err
		}
		sf.Regs[bank] = b
	}
	return &sf, nil
}

func SaveState(path string, sf *StateFile) error {
	sf.RegHex = HexMap(sf.Regs)
	raw, err := json.MarshalIndent(sf, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
