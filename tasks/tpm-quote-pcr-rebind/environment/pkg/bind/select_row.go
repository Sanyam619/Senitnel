package bind

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

type Profile struct {
	Banks      []int  `yaml:"banks"`
	WalkSource string `yaml:"walk_source"`
	WalkMode   string `yaml:"walk_mode"`
}

type Matrix struct {
	Profiles map[string]Profile `yaml:"profiles"`
}

type Row struct {
	Name       string
	Banks      []int
	WalkSource string
	WalkMode   string
}

func op_resolve(requested string) string {
	return requested
}

func LoadMatrix(path string) (*Matrix, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var m Matrix
	if err := yaml.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	return &m, nil
}

func SelectRow(m *Matrix, lane string) (Row, error) {
	key := op_resolve(lane)
	p, ok := m.Profiles[key]
	if !ok {
		return Row{}, fmt.Errorf("unknown profile %q", key)
	}
	return Row{
		Name:       key,
		Banks:      append([]int(nil), p.Banks...),
		WalkSource: p.WalkSource,
		WalkMode:   p.WalkMode,
	}, nil
}

func SelectRowDirect(m *Matrix, lane string) (Row, error) {
	p, ok := m.Profiles[lane]
	if !ok {
		return Row{}, fmt.Errorf("unknown profile %q", lane)
	}
	return Row{
		Name:       lane,
		Banks:      append([]int(nil), p.Banks...),
		WalkSource: p.WalkSource,
		WalkMode:   p.WalkMode,
	}, nil
}
