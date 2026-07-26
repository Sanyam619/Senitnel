package tree

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func EnsureDir(dir string) error {
	return os.MkdirAll(dir, 0o755)
}

func WriteLeaf(dir, leaf, body string) error {
	if err := EnsureDir(dir); err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dir, leaf), []byte(body+"\n"), 0o644)
}

func AppendSubtree(dir string, add []string) error {
	cur, err := ReadTokens(dir, "cgroup.subtree_control")
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	seen := map[string]bool{}
	for _, t := range cur {
		seen[t] = true
	}
	for _, t := range add {
		t = strings.TrimSpace(t)
		if t == "" || seen[t] {
			continue
		}
		seen[t] = true
		cur = append(cur, t)
	}
	body := strings.Join(cur, " ")
	if body == "" {
		body = strings.Join(add, " ")
	}
	return WriteLeaf(dir, "cgroup.subtree_control", body)
}

func PropagateControllers(parent string) error {
	tokens, err := ReadTokens(parent, "cgroup.subtree_control")
	if err != nil {
		return err
	}
	entries, err := os.ReadDir(parent)
	if err != nil {
		return err
	}
	for _, ent := range entries {
		if !ent.IsDir() {
			continue
		}
		child := filepath.Join(parent, ent.Name())
		ctrl, _ := ReadFile(child, "cgroup.controllers")
		if ctrl == "" {
			base, _ := ReadFile(parent, "cgroup.controllers")
			_ = WriteLeaf(child, "cgroup.controllers", base)
		}
		sub, _ := ReadFile(child, "cgroup.subtree_control")
		if sub == "" && len(tokens) > 0 {
			_ = WriteLeaf(child, "cgroup.subtree_control", "")
		}
	}
	return nil
}

func ApplyBrakeMap(dir string, brakes map[string]string) error {
	for leaf, val := range brakes {
		if err := WriteLeaf(dir, leaf, val); err != nil {
			return fmt.Errorf("write %s: %w", leaf, err)
		}
	}
	return nil
}
