package trace

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"rly/internal/chip"
)

func reconcile_a(source string, root string) ([]chip.Step, error) {
	path := filepath.Join(root, source+".evt")
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var steps []chip.Step
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		var s chip.Step
		if err := json.Unmarshal(sc.Bytes(), &s); err != nil {
			return nil, fmt.Errorf("parse line: %w", err)
		}
		steps = append(steps, s)
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	return steps, nil
}

func LoadSteps(source, root string) ([]chip.Step, error) {
	return reconcile_a(source, root)
}

func LoadStepsDirect(source, root string) ([]chip.Step, error) {
	return reconcile_a(source, root)
}
