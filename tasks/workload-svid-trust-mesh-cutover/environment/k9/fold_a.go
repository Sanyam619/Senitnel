package k9

import (
	"encoding/json"
	"os"
)

// fold_a publishes the live bundle from runtime + root material.
// a: runtime.json path; b: live-bundle.json path
func fold_a(a string, b string) error {
	rt, err := load_rt(a)
	if err != nil {
		return err
	}
	rootsRaw, err := os.ReadFile("/app/data/material/roots.json")
	if err != nil {
		return err
	}
	var roots struct {
		Roots map[string]struct {
			Kid        string `json:"kid"`
			Generation int    `json:"generation"`
		} `json:"roots"`
	}
	if err := json.Unmarshal(rootsRaw, &roots); err != nil {
		return err
	}
	root := rt.TargetRoot
	if root == "" {
		root = "root-b"
	}
	meta, ok := roots.Roots[root]
	if !ok {
		return os.ErrInvalid
	}
	return store_lv(b, liveView{
		ActiveRoot: root,
		Epoch:      rt.Epoch,
		Kid:        meta.Kid,
		Generation: meta.Generation,
	})
}
