package audit

import (
	"encoding/json"
	"os"
)

type Step struct {
	Tool   string `json:"tool"`
	Action string `json:"action"`
}

type Trace struct {
	Version int    `json:"version"`
	Steps   []Step `json:"steps"`
}

func Write(path string, steps []Step) error {
	payload := Trace{Version: 1, Steps: steps}
	data, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func AppendStep(path string, step Step) error {
	var trace Trace
	raw, err := os.ReadFile(path)
	if err != nil {
		trace = Trace{Version: 1, Steps: []Step{}}
	} else if err := json.Unmarshal(raw, &trace); err != nil {
		return err
	}
	trace.Steps = append(trace.Steps, step)
	return Write(path, trace.Steps)
}
