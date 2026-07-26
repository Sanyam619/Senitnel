package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"packlab/internal/blob"
	"packlab/internal/descript"
	"packlab/internal/layerwire"
	"packlab/internal/emit"
	"packlab/internal/overlay"

	"github.com/opencontainers/go-digest"
)

func main() {
	root := flag.String("root", "/data/images", "bundle root")
	out := flag.String("out", "/output/reconcile-report.json", "report path")
	flag.Parse()

	ids, err := listBundles(*root)
	if err != nil {
		fmt.Fprintf(os.Stderr, "list: %v\n", err)
		os.Exit(1)
	}
	var rows []emit.Row
	for _, id := range ids {
		row, err := reconcileBundle(*root, id)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: %v\n", id, err)
			os.Exit(1)
		}
		rows = append(rows, row)
	}
	if err := emit.Write(*out, rows); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(1)
	}
}

func listBundles(root string) ([]string, error) {
	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}
	var ids []string
	for _, e := range entries {
		if e.IsDir() {
			ids = append(ids, e.Name())
		}
	}
	sort.Strings(ids)
	return ids, nil
}

func reconcileBundle(root, id string) (emit.Row, error) {
	meta, err := descript.LoadMeta(root, id)
	if err != nil {
		return emit.Row{}, err
	}
	blobs := map[digest.Digest][]byte{}
	for _, d := range meta.Manifest {
		b, err := blob.Load(filepath.Join(root, id), d)
		if err != nil {
			return emit.Row{}, err
		}
		blobs[d] = b
	}
	order, err := layerwire.BuildStack(meta.Manifest, meta.WireIDs, blobs)
	if err != nil {
		return emit.Row{}, err
	}
	var rawLayers [][]byte
	var stacks []string
	for _, d := range order {
		payload := blobs[d]
		raw, err := layerwire.Gunzip(payload)
		if err != nil {
			return emit.Row{}, err
		}
		rawLayers = append(rawLayers, raw)
		stacks = append(stacks, d.String())
	}
	merged := overlay.ApplyLayers(rawLayers)
	return emit.Row{
		ID:     id,
		Stacks: stacks,
		Paths:  emit.PathsFromMerged(merged),
	}, nil
}
