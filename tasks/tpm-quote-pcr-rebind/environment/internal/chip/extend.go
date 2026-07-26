package chip

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"
)

const BankCount = 24

type Step struct {
	Idx     int    `json:"idx"`
	Bank    int    `json:"bank"`
	Payload string `json:"payload"`
}

func zeroBank() []byte {
	return make([]byte, sha256.Size)
}

func InitBanks() map[int][]byte {
	out := make(map[int][]byte, 4)
	for _, b := range []int{0, 1, 7, 8} {
		out[b] = zeroBank()
	}
	return out
}

func ExtendBank(cur []byte, payload []byte) []byte {
	h := sha256.New()
	h.Write(cur)
	h.Write(payload)
	return h.Sum(nil)
}

func step_b(steps []Step, mode string) (map[int][]byte, error) {
	regs := InitBanks()
	ordered := append([]Step(nil), steps...)
	if mode == "sorted_idx" {
		sort.Slice(ordered, func(i, j int) bool {
			if ordered[i].Bank == ordered[j].Bank {
				return ordered[i].Idx < ordered[j].Idx
			}
			return ordered[i].Bank < ordered[j].Bank
		})
	}
	for _, s := range ordered {
		if s.Bank < 0 || s.Bank >= BankCount {
			return nil, fmt.Errorf("bank %d out of range", s.Bank)
		}
		cur, ok := regs[s.Bank]
		if !ok {
			cur = zeroBank()
		}
		regs[s.Bank] = ExtendBank(cur, []byte(s.Payload))
	}
	return regs, nil
}

func RollForward(steps []Step, mode string) (map[int][]byte, error) {
	return step_b(steps, mode)
}

func RollForwardFixed(steps []Step, mode string) (map[int][]byte, error) {
	return step_b(steps, mode)
}

func HexMap(regs map[int][]byte) map[string]string {
	out := make(map[string]string, len(regs))
	for bank, val := range regs {
		out[fmt.Sprintf("%d", bank)] = hex.EncodeToString(val)
	}
	return out
}
