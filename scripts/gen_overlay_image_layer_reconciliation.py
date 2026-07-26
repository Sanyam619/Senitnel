#!/usr/bin/env python3
"""One-shot generator for tasks/overlay-image-layer-reconciliation (authoring tool, not shipped)."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import tarfile
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "overlay-image-layer-reconciliation"
LAB = "/opt/packlab"
DATA = "/data/images"
CANONICAL_GOLANG = "public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac"

BUNDLES = ("bundle-x7", "bundle-m4", "bundle-k9", "bundle-r2", "bundle-n5")


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def wbin(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_pref(data: bytes) -> str:
    return f"sha256:{sha256_hex(data)}"


def content_digest(data: bytes) -> str:
    return sha256_pref(data)


@dataclass
class TarSpec:
    path: str
    kind: Literal["file", "whiteout", "opaque", "dir", "link"]
    data: bytes = b""
    link_target: str = ""


def build_tar(specs: list[TarSpec]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for spec in specs:
            if spec.kind == "dir":
                ti = tarfile.TarInfo(spec.path)
                ti.type = tarfile.DIRTYPE
                ti.mode = 0o755
                ti.uid = 0
                ti.gid = 0
                ti.uname = "root"
                ti.gname = "root"
                tar.addfile(ti)
                continue
            if spec.kind == "whiteout":
                ti = tarfile.TarInfo(spec.path)
                ti.type = tarfile.REGTYPE
                ti.size = 0
                ti.mode = 0o644
                tar.addfile(ti, io.BytesIO(b""))
                continue
            if spec.kind == "opaque":
                ti = tarfile.TarInfo(spec.path)
                ti.type = tarfile.REGTYPE
                ti.size = 0
                ti.mode = 0o644
                tar.addfile(ti, io.BytesIO(b""))
                continue
            if spec.kind == "link":
                ti = tarfile.TarInfo(spec.path)
                ti.type = tarfile.LNKTYPE
                ti.linkname = spec.link_target
                ti.mode = 0o644
                tar.addfile(ti)
                continue
            ti = tarfile.TarInfo(spec.path)
            ti.type = tarfile.REGTYPE
            ti.size = len(spec.data)
            ti.mode = 0o644
            ti.uid = 0
            ti.gid = 0
            ti.uname = "root"
            ti.gname = "root"
            tar.addfile(ti, io.BytesIO(spec.data))
    return buf.getvalue()


@dataclass
class LayerBlob:
    gzip_bytes: bytes
    diff_id: str
    digest: str


def layer_from_specs(specs: list[TarSpec]) -> LayerBlob:
    raw = build_tar(specs)
    diff_id = sha256_pref(raw)
    gz = gzip.compress(raw, compresslevel=9)
    return LayerBlob(gzip_bytes=gz, diff_id=diff_id, digest=sha256_pref(gz))


@dataclass
class BundleSpec:
    bundle_id: str
    layers: list[LayerBlob]
    manifest_order: list[int]
    orphan_digest: str | None = None


def parse_tar_entries(raw: bytes) -> list[tuple[str, str, bytes, str]]:
    entries: list[tuple[str, str, bytes, str]] = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
        for member in tar.getmembers():
            if member.isdir():
                entries.append((member.name, "dir", b"", ""))
                continue
            if member.issym() or member.islnk():
                entries.append((member.name, "link", b"", member.linkname))
                continue
            f = tar.extractfile(member)
            payload = f.read() if f else b""
            base = member.name.rsplit("/", 1)[-1]
            parent = member.name.rsplit("/", 1)[0] if "/" in member.name else ""
            if base.startswith(".wh."):
                if base == ".wh..wh..opq":
                    entries.append((member.name, "opaque", b"", ""))
                else:
                    entries.append((member.name, "whiteout", b"", parent))
                continue
            entries.append((member.name, "file", payload, ""))
    return entries


def flatten_bottom_to_top(layers_raw: list[bytes]) -> dict[str, bytes]:
    merged: dict[str, bytes] = {}
    for raw in layers_raw:
        entries = parse_tar_entries(raw)
        opaque_dirs: list[str] = []
        whiteouts: list[tuple[str, str]] = []
        regular: list[tuple[str, bytes]] = []
        links: list[tuple[str, str]] = []

        for path, kind, payload, extra in entries:
            if kind == "opaque":
                opaque_dirs.append(path.rsplit("/", 1)[0] if "/" in path else "")
            elif kind == "whiteout":
                parent = extra
                target = path.rsplit("/", 1)[-1][4:]
                whiteouts.append((parent, target))
            elif kind == "link":
                links.append((path, extra))
            elif kind == "file":
                regular.append((path, payload))

        for op_dir in opaque_dirs:
            prefix = f"{op_dir}/" if op_dir else ""
            drop = {k for k in merged if (op_dir == "" and "/" not in k) or k.startswith(prefix)}
            for key in drop:
                merged.pop(key, None)

        for parent, target in whiteouts:
            full = f"{parent}/{target}" if parent else target
            merged.pop(full, None)

        for path, payload in regular:
            merged[path] = payload

        for path, target in links:
            if target in merged:
                merged[path] = merged[target]

    return merged


def canonical_stack_indices(spec: BundleSpec) -> list[int]:
    return list(range(len(spec.layers)))


def build_bundles() -> tuple[dict[str, BundleSpec], dict[str, dict]]:
    x7_l0 = layer_from_specs([TarSpec("etc/seed", "file", b"base-seed\n")])
    x7_l1 = layer_from_specs([TarSpec("app/mid.txt", "file", b"mid-tier\n")])
    x7_l2 = layer_from_specs([TarSpec("app/top.txt", "file", b"top-tier\n")])
    x7 = BundleSpec("bundle-x7", [x7_l0, x7_l1, x7_l2], manifest_order=[2, 0, 1])

    m4_l0 = layer_from_specs(
        [
            TarSpec("var/www", "dir"),
            TarSpec("var/www/index.html", "file", b"<html>old</html>\n"),
            TarSpec("var/www/stale.html", "file", b"stale\n"),
        ]
    )
    m4_l1 = layer_from_specs(
        [
            TarSpec("var/www/.wh.stale.html", "whiteout"),
            TarSpec("var/www/leaf.txt", "file", b"leaf\n"),
        ]
    )
    m4_l2 = layer_from_specs(
        [
            TarSpec("var/www/.wh..wh..opq", "opaque"),
            TarSpec("var/www/index.html", "file", b"<html>fresh</html>\n"),
        ]
    )
    m4 = BundleSpec("bundle-m4", [m4_l0, m4_l1, m4_l2], manifest_order=[1, 2, 0])

    k9_l0 = layer_from_specs([TarSpec("data/payload", "file", b"SHARED-BYTES\n")])
    k9_l1 = layer_from_specs([TarSpec("data/alias", "link", link_target="data/payload")])
    k9_l2 = layer_from_specs([TarSpec("data/note.txt", "file", b"annotation\n")])
    orphan = layer_from_specs([TarSpec("orphan/only.txt", "file", b"never-linked\n")])
    k9 = BundleSpec(
        "bundle-k9",
        [k9_l0, k9_l1, k9_l2],
        manifest_order=[0, 2, 1],
        orphan_digest=orphan.digest,
    )

    r2_l0 = layer_from_specs(
        [
            TarSpec("var/log/app.log", "file", b"v1\n"),
            TarSpec("var/log/archive/trail.txt", "file", b"old-trail\n"),
        ]
    )
    r2_l1 = layer_from_specs(
        [
            TarSpec("var/log/archive/.wh.trail.txt", "whiteout"),
            TarSpec("var/log/app.log", "file", b"v2\n"),
        ]
    )
    r2_l2 = layer_from_specs(
        [
            TarSpec("var/log/.wh..wh..opq", "opaque"),
            TarSpec("var/log/app.log", "file", b"v3\n"),
        ]
    )
    r2 = BundleSpec("bundle-r2", [r2_l0, r2_l1, r2_l2], manifest_order=[2, 0, 1])

    n5_l0 = layer_from_specs(
        [
            TarSpec("share/core.dat", "file", b"CORE-v1\n"),
            TarSpec("share/readme.txt", "file", b"readme\n"),
        ]
    )
    n5_l1 = layer_from_specs([TarSpec("share/mirror", "link", link_target="share/core.dat")])
    n5_l2 = layer_from_specs(
        [
            TarSpec("share/.wh.readme.txt", "whiteout"),
            TarSpec("share/core.dat", "file", b"CORE-v2\n"),
        ]
    )
    orphan_n5 = layer_from_specs([TarSpec("staging/unused.bin", "file", b"never\n")])
    n5 = BundleSpec(
        "bundle-n5",
        [n5_l0, n5_l1, n5_l2],
        manifest_order=[1, 2, 0],
        orphan_digest=orphan_n5.digest,
    )

    specs = {x7.bundle_id: x7, m4.bundle_id: m4, k9.bundle_id: k9, r2.bundle_id: r2, n5.bundle_id: n5}
    gold: dict[str, dict] = {}
    for bid, spec in specs.items():
        order = canonical_stack_indices(spec)
        raw_layers = []
        stacks = []
        for idx in order:
            raw = gzip.decompress(spec.layers[idx].gzip_bytes)
            raw_layers.append(raw)
            stacks.append(spec.layers[idx].digest)
        paths = {p: content_digest(b) for p, b in sorted(flatten_bottom_to_top(raw_layers).items())}
        gold[bid] = {"stacks": stacks, "paths": paths}
    return specs, gold


GO_MOD = """module packlab

go 1.22

require github.com/opencontainers/go-digest v1.0.0
"""

OP_A_GO = """package layerwire

import (
\t"crypto/sha256"
\t"encoding/hex"
\t"fmt"
\t"sort"

\t"github.com/opencontainers/go-digest"
)

// BuildStack materializes the blob digest stack for one bundle.
func BuildStack(manifestDigests []digest.Digest, wireIDs []digest.Digest, blobs map[digest.Digest][]byte) ([]digest.Digest, error) {
\tif len(manifestDigests) == 0 {
\t\treturn nil, fmt.Errorf("empty manifest")
\t}
\t_ = wireIDs
\tout := append([]digest.Digest(nil), manifestDigests...)
\tsort.SliceStable(out, func(i, j int) bool {
\t\treturn out[i].String() < out[j].String()
\t})
\tfor _, d := range out {
\t\tif _, ok := blobs[d]; !ok {
\t\t\treturn nil, fmt.Errorf("missing blob %s", d)
\t\t}
\t}
\treturn out, nil
}

func WireMatch(blob []byte, want digest.Digest) bool {
\traw, err := gunzip(blob)
\tif err != nil {
\t\treturn false
\t}
\th := sha256.Sum256(raw)
\tgot := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
\treturn got == want
}

func gunzip(b []byte) ([]byte, error) {
\treturn gzipDecompress(b)
}
"""

OP_A_GO_FIXED = """package layerwire

import (
\t"crypto/sha256"
\t"encoding/hex"
\t"fmt"

\t"github.com/opencontainers/go-digest"
)

// BuildStack materializes the blob digest stack bottom-to-top from chain metadata.
func BuildStack(manifestDigests []digest.Digest, wireIDs []digest.Digest, blobs map[digest.Digest][]byte) ([]digest.Digest, error) {
\tif len(wireIDs) == 0 {
\t\treturn nil, fmt.Errorf("empty wire chain")
\t}
\tdiffToBlob := map[digest.Digest]digest.Digest{}
\tfor _, md := range manifestDigests {
\t\tpayload, ok := blobs[md]
\t\tif !ok {
\t\t\tcontinue
\t\t}
\t\traw, err := gunzip(payload)
\t\tif err != nil {
\t\t\treturn nil, err
\t\t}
\t\th := sha256.Sum256(raw)
\t\tdiff := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
\t\tdiffToBlob[diff] = md
\t}
\tout := make([]digest.Digest, 0, len(wireIDs))
\tfor _, wid := range wireIDs {
\t\tbd, ok := diffToBlob[wid]
\t\tif !ok {
\t\t\treturn nil, fmt.Errorf("no blob for wire id %s", wid)
\t\t}
\t\tout = append(out, bd)
\t}
\treturn out, nil
}

func WireMatch(blob []byte, want digest.Digest) bool {
\traw, err := gunzip(blob)
\tif err != nil {
\t\treturn false
\t}
\th := sha256.Sum256(raw)
\tgot := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
\treturn got == want
}

func gunzip(b []byte) ([]byte, error) {
\treturn gzipDecompress(b)
}
"""

RECONCILE_B_GO = """package overlay

import (
\t"archive/tar"
\t"bytes"
\t"compress/gzip"
\t"io"
\t"sort"

\t"github.com/opencontainers/go-digest"
)

type Entry struct {
\tPath string
\tKind string
\tBody []byte
\tLink string
}

// ApplyLayers folds unpacked tar payloads into a merged path map.
func ApplyLayers(layers [][]byte) map[string][]byte {
\tmerged := map[string][]byte{}
\tfor _, raw := range layers {
\t\tentries := readEntries(raw)
\t\tfor _, e := range entries {
\t\t\tif e.Kind == "whiteout" {
\t\t\t\tdelete(merged, e.Path)
\t\t\t\tcontinue
\t\t\t}
\t\t\tif e.Kind == "file" {
\t\t\t\tmerged[e.Path] = append([]byte(nil), e.Body...)
\t\t\t}
\t\t}
\t}
\treturn merged
}

func readEntries(raw []byte) []Entry {
\tvar out []Entry
\tgr, err := gzip.NewReader(bytes.NewReader(raw))
\tif err == nil {
\t\tdefer gr.Close()
\t\traw, _ = io.ReadAll(gr)
\t}
\ttr := tar.NewReader(bytes.NewReader(raw))
\tfor {
\t\th, err := tr.Next()
\t\tif err == io.EOF {
\t\t\tbreak
\t\t}
\t\tif err != nil {
\t\t\tbreak
\t\t}
\t\tname := h.Name
\t\tbase := name
\t\tif i := len(name) - 1; i >= 0 {
\t\t\tfor j := i; j >= 0; j-- {
\t\t\t\tif name[j] == '/' {
\t\t\t\t\tbase = name[j+1:]
\t\t\t\t\tbreak
\t\t\t\t}
\t\t\t}
\t\t}
\t\tif h.Typeflag == tar.TypeDir {
\t\t\tcontinue
\t\t}
\t\tif h.Typeflag == tar.TypeLink || h.Typeflag == tar.TypeSymlink {
\t\t\tout = append(out, Entry{Path: name, Kind: "link", Link: h.Linkname})
\t\t\tcontinue
\t\t}
\t\tif len(base) > 4 && base[:4] == ".wh." {
\t\t\tif base == ".wh..wh..opq" {
\t\t\t\tout = append(out, Entry{Path: name, Kind: "opaque"})
\t\t\t\tcontinue
\t\t\t}
\t\t\tparent := ""
\t\t\tif idx := len(name) - len(base) - 1; idx > 0 {
\t\t\t\tparent = name[:idx]
\t\t\t}
\t\t\ttarget := base[4:]
\t\t\tfull := target
\t\t\tif parent != "" {
\t\t\t\tfull = parent + "/" + target
\t\t\t}
\t\t\tout = append(out, Entry{Path: full, Kind: "whiteout"})
\t\t\tcontinue
\t\t}
\t\tbody, _ := io.ReadAll(tr)
\t\tout = append(out, Entry{Path: name, Kind: "file", Body: body})
\t}
\tsort.Slice(out, func(i, j int) bool { return out[i].Path < out[j].Path })
\treturn out
}

func PathDigest(data []byte) digest.Digest {
\treturn digest.FromBytes(data)
}
"""

RECONCILE_B_GO_FIXED = RECONCILE_B_GO.replace(
    """// ApplyLayers folds unpacked tar payloads into a merged path map.
func ApplyLayers(layers [][]byte) map[string][]byte {
\tmerged := map[string][]byte{}
\tfor _, raw := range layers {
\t\tentries := readEntries(raw)
\t\tfor _, e := range entries {
\t\t\tif e.Kind == "whiteout" {
\t\t\t\tdelete(merged, e.Path)
\t\t\t\tcontinue
\t\t\t}
\t\t\tif e.Kind == "file" {
\t\t\t\tmerged[e.Path] = append([]byte(nil), e.Body...)
\t\t\t}
\t\t}
\t}
\treturn merged
}""",
    """// ApplyLayers folds unpacked tar payloads bottom-to-top across marker rows.
func ApplyLayers(layers [][]byte) map[string][]byte {
\tmerged := map[string][]byte{}
\tfor _, raw := range layers {
\t\tentries := readEntries(raw)
\t\tvar opaqueDirs []string
\t\tvar whiteouts []string
\t\tvar files []Entry
\t\tvar links []Entry
\t\tfor _, e := range entries {
\t\t\tswitch e.Kind {
\t\t\tcase "opaque":
\t\t\t\topaqueDirs = append(opaqueDirs, parentDir(e.Path))
\t\t\tcase "whiteout":
\t\t\t\twhiteouts = append(whiteouts, e.Path)
\t\t\tcase "file":
\t\t\t\tfiles = append(files, e)
\t\t\tcase "link":
\t\t\t\tlinks = append(links, e)
\t\t\t}
\t\t}
\t\tfor _, dir := range opaqueDirs {
\t\t\tprefix := dir + "/"
\t\t\tfor k := range merged {
\t\t\t\tif dir == "" {
\t\t\t\t\tif !containsSlash(k) {
\t\t\t\t\t\tdelete(merged, k)
\t\t\t\t\t}
\t\t\t\t} else if k == dir || len(k) > len(prefix) && k[:len(prefix)] == prefix {
\t\t\t\t\tdelete(merged, k)
\t\t\t\t}
\t\t\t}
\t\t}
\t\tfor _, p := range whiteouts {
\t\t\tdelete(merged, p)
\t\t}
\t\tfor _, e := range files {
\t\t\tmerged[e.Path] = append([]byte(nil), e.Body...)
\t\t}
\t\tfor _, e := range links {
\t\t\tif body, ok := merged[e.Link]; ok {
\t\t\t\tmerged[e.Path] = append([]byte(nil), body...)
\t\t\t}
\t\t}
\t}
\treturn merged
}

func parentDir(p string) string {
\tif i := len(p) - 1; i >= 0 {
\t\tfor j := i; j >= 0; j-- {
\t\t\tif p[j] == '/' {
\t\t\t\treturn p[:j]
\t\t\t}
\t\t}
\t}
\treturn ""
}

func containsSlash(s string) bool {
\tfor i := 0; i < len(s); i++ {
\t\tif s[i] == '/' {
\t\t\treturn true
\t\t}
\t}
\treturn false
}""",
)

RESOLVE_C_GO = """package descript

import (
\t"encoding/json"
\t"fmt"
\t"os"
\t"path/filepath"

\t"github.com/opencontainers/go-digest"
)

type Descriptor struct {
\tDigest digest.Digest `json:"digest"`
\tSize   int64         `json:"size"`
}

type WireConfig struct {
\tRootFS struct {
\t\tType     string           `json:"type"`
\t\tDiffIDs  []digest.Digest  `json:"diff_ids"`
\t} `json:"rootfs"`
}

type Bundle struct {
\tID       string
\tManifest []digest.Digest
\tWireIDs  []digest.Digest
}

// LoadMeta reads descriptor JSON for a bundle tree.
func LoadMeta(root, id string) (Bundle, error) {
\tbase := filepath.Join(root, id)
\tvar man struct {
\t\tLayers []Descriptor `json:"layers"`
\t}
\tmb, err := os.ReadFile(filepath.Join(base, "index.json"))
\tif err != nil {
\t\treturn Bundle{}, err
\t}
\tif err := json.Unmarshal(mb, &man); err != nil {
\t\treturn Bundle{}, err
\t}
\tcb, err := os.ReadFile(filepath.Join(base, "wire.json"))
\tif err != nil {
\t\treturn Bundle{}, err
\t}
\tvar wire WireConfig
\tif err := json.Unmarshal(cb, &wire); err != nil {
\t\treturn Bundle{}, err
\t}
\torder := make([]digest.Digest, 0, len(man.Layers))
\tfor _, layer := range man.Layers {
\t\torder = append(order, layer.Digest)
\t}
\tif len(order) == 0 {
\t\treturn Bundle{}, fmt.Errorf("empty manifest for %s", id)
\t}
\treturn Bundle{ID: id, Manifest: order, WireIDs: wire.RootFS.DiffIDs}, nil
}
"""

RESOLVE_C_GO_FIXED = """package descript

import (
\t"bytes"
\t"compress/gzip"
\t"crypto/sha256"
\t"encoding/hex"
\t"encoding/json"
\t"fmt"
\t"io"
\t"os"
\t"path/filepath"

\t"github.com/opencontainers/go-digest"
)

type Descriptor struct {
\tDigest digest.Digest `json:"digest"`
\tSize   int64         `json:"size"`
}

type WireConfig struct {
\tRootFS struct {
\t\tType     string           `json:"type"`
\t\tDiffIDs  []digest.Digest  `json:"diff_ids"`
\t} `json:"rootfs"`
}

type Bundle struct {
\tID       string
\tManifest []digest.Digest
\tWireIDs  []digest.Digest
}

// LoadMeta reads descriptor JSON and retains only rows tied to the chain file.
func LoadMeta(root, id string) (Bundle, error) {
\tbase := filepath.Join(root, id)
\tvar man struct {
\t\tLayers []Descriptor `json:"layers"`
\t}
\tmb, err := os.ReadFile(filepath.Join(base, "index.json"))
\tif err != nil {
\t\treturn Bundle{}, err
\t}
\tif err := json.Unmarshal(mb, &man); err != nil {
\t\treturn Bundle{}, err
\t}
\tcb, err := os.ReadFile(filepath.Join(base, "wire.json"))
\tif err != nil {
\t\treturn Bundle{}, err
\t}
\tvar wire WireConfig
\tif err := json.Unmarshal(cb, &wire); err != nil {
\t\treturn Bundle{}, err
\t}
\twireSet := map[digest.Digest]struct{}{}
\tfor _, wid := range wire.RootFS.DiffIDs {
\t\twireSet[wid] = struct{}{}
\t}
\torder := make([]digest.Digest, 0, len(man.Layers))
\tfor _, layer := range man.Layers {
\t\tpayload, err := os.ReadFile(filepath.Join(base, "blobs", "sha256", layer.Digest.Encoded()))
\t\tif err != nil {
\t\t\tcontinue
\t\t}
\t\traw, err := gunzipLocal(payload)
\t\tif err != nil {
\t\t\tcontinue
\t\t}
\t\th := sha256.Sum256(raw)
\t\tdiff := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
\t\tif _, ok := wireSet[diff]; ok {
\t\t\torder = append(order, layer.Digest)
\t\t}
\t}
\tif len(order) == 0 {
\t\treturn Bundle{}, fmt.Errorf("empty manifest for %s", id)
\t}
\treturn Bundle{ID: id, Manifest: order, WireIDs: wire.RootFS.DiffIDs}, nil
}

func gunzipLocal(b []byte) ([]byte, error) {
\tgr, err := gzip.NewReader(bytes.NewReader(b))
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer gr.Close()
\treturn io.ReadAll(gr)
}
"""


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)

    specs, gold = build_bundles()

    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "system-administration"
subcategories = ["tool_specific"]
number_of_milestones = 0
codebase_size = "small"
languages = ["go", "bash"]
tags = ["containers", "go", "packaging", "ops", "storage", "integrity"]
expert_time_estimate_min = 180
junior_time_estimate_min = 420

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
""",
    )

    w(
        TASK / "instruction.md",
        f"""Five bundle trees under `{DATA}/` were copied in for a packaging QA sweep (see `{LAB}/config/lab.toml` for the bundle id list). Each tree pairs JSON descriptors with gzipped tar blobs. Preview tooling and the production emitter both run without crashing, yet QA keeps rejecting runs because stack digests and per-path content fingerprints in `/output/reconcile-report.json` diverge from what you get when you unpack the blobs yourself on several bundles.

Repair the lab sources under `{LAB}`, rebuild `{LAB}/bin/packctl`, and regenerate the report. The JSON must stay at version 1 with one `bundles[]` row per bundle id from the config, each carrying `id`, a bottom-to-top `stacks` list of blob digests, and a `paths` map from relative paths to `sha256:` content digests for the merged view. Do not touch anything under `{DATA}/`; `anchor.sha256` there is the integrity ledger for inputs.
""",
    )

    w(
        TASK / "output_contract.toml",
        """user_visible_outputs = [
  "/output/reconcile-report.json",
]

internal_harness_files = [
  "/tests/test_outputs.py",
]

[structured_outputs.reconcile_report]
target = "/output/reconcile-report.json"
format = "json"
instruction_checks = [
  "version",
  "bundles",
  "stacks",
  "paths",
]
""",
    )

    # --- environment go sources ---
    w(TASK / "environment" / "go.mod", GO_MOD)
    w(TASK / "environment" / "go.sum", "")

    w(
        TASK / "environment" / "internal" / "layerwire" / "gzip.go",
        """package layerwire

import (
\t"bytes"
\t"compress/gzip"
\t"io"
)

func gzipDecompress(b []byte) ([]byte, error) {
\tgr, err := gzip.NewReader(bytes.NewReader(b))
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer gr.Close()
\treturn io.ReadAll(gr)
}
""",
    )
    w(TASK / "environment" / "internal" / "layerwire" / "seq.go", OP_A_GO)
    w(TASK / "environment" / "internal" / "overlay" / "merge.go", RECONCILE_B_GO)
    w(TASK / "environment" / "internal" / "descript" / "bundle.go", RESOLVE_C_GO)

    w(
        TASK / "environment" / "internal" / "digest" / "hash_e.go",
        """package digestx

import (
\t"crypto/sha256"
\t"encoding/hex"

\t"github.com/opencontainers/go-digest"
)

func FromBytes(b []byte) digest.Digest {
\th := sha256.Sum256(b)
\treturn digest.Digest("sha256:" + hex.EncodeToString(h[:]))
}
""",
    )

    w(
        TASK / "environment" / "pkg" / "graph" / "walk_d.go",
        """package graph

import "github.com/opencontainers/go-digest"

// WalkD performs a depth-first walk over adjacency rows (telemetry only).
func WalkD(adj map[digest.Digest][]digest.Digest, start digest.Digest) []digest.Digest {
\tseen := map[digest.Digest]struct{}{}
\tvar out []digest.Digest
\tvar visit func(d digest.Digest)
\tvisit = func(d digest.Digest) {
\t\tif _, ok := seen[d]; ok {
\t\t\treturn
\t\t}
\t\tseen[d] = struct{}{}
\t\tout = append(out, d)
\t\tfor _, n := range adj[d] {
\t\t\tvisit(n)
\t\t}
\t}
\tvisit(start)
\treturn out
}
""",
    )

    w(
        TASK / "environment" / "internal" / "blob" / "store.go",
        """package blob

import (
\t"fmt"
\t"os"
\t"path/filepath"

\t"github.com/opencontainers/go-digest"
)

func Load(dir string, d digest.Digest) ([]byte, error) {
\tpath := filepath.Join(dir, "blobs", "sha256", d.Encoded())
\tb, err := os.ReadFile(path)
\tif err != nil {
\t\treturn nil, fmt.Errorf("read %s: %w", path, err)
\t}
\treturn b, nil
}
""",
    )

    w(
        TASK / "environment" / "internal" / "emit" / "report.go",
        """package emit

import (
\t"encoding/json"
\t"os"

\t"packlab/internal/overlay"
)

type Row struct {
\tID     string            `json:"id"`
\tStacks []string          `json:"stacks"`
\tPaths  map[string]string `json:"paths"`
}

type Doc struct {
\tVersion int   `json:"version"`
\tBundles  []Row `json:"bundles"`
}

func Write(path string, rows []Row) error {
\tdoc := Doc{Version: 1, Bundles: rows}
\tfor i := range doc.Bundles {
\t\tif doc.Bundles[i].Paths == nil {
\t\t\tdoc.Bundles[i].Paths = map[string]string{}
\t\t}
\t}
\tb, err := json.MarshalIndent(doc, "", "  ")
\tif err != nil {
\t\treturn err
\t}
\treturn os.WriteFile(path, append(b, '\\n'), 0o644)
}

func PathsFromMerged(merged map[string][]byte) map[string]string {
\tout := make(map[string]string, len(merged))
\tfor k, v := range merged {
\t\tout[k] = overlay.PathDigest(v).String()
\t}
\treturn out
}
""",
    )

    list_bundles_broken = """func listBundles(root string) ([]string, error) {
\tentries, err := os.ReadDir(root)
\tif err != nil {
\t\treturn nil, err
\t}
\tvar ids []string
\tfor _, e := range entries {
\t\tif e.IsDir() {
\t\t\tids = append(ids, e.Name())
\t\t}
\t}
\tsort.Strings(ids)
\treturn ids, nil
}"""

    list_bundles_fixed = """func listBundles(root string) ([]string, error) {
\tentries, err := os.ReadDir(root)
\tif err != nil {
\t\treturn nil, err
\t}
\tvar ids []string
\tfor _, e := range entries {
\t\tif !e.IsDir() {
\t\t\tcontinue
\t\t}
\t\tname := e.Name()
\t\tbase := filepath.Join(root, name)
\t\tif _, err := os.Stat(filepath.Join(base, "index.json")); err != nil {
\t\t\tcontinue
\t\t}
\t\tif _, err := os.Stat(filepath.Join(base, "wire.json")); err != nil {
\t\t\tcontinue
\t\t}
\t\tids = append(ids, name)
\t}
\tsort.Strings(ids)
\treturn ids, nil
}"""

    packctl_main_body = f"""package main

import (
\t"flag"
\t"fmt"
\t"os"
\t"path/filepath"
\t"sort"

\t"packlab/internal/blob"
\t"packlab/internal/descript"
\t"packlab/internal/layerwire"
\t"packlab/internal/emit"
\t"packlab/internal/overlay"

\t"github.com/opencontainers/go-digest"
)

func main() {{
\troot := flag.String("root", "{DATA}", "bundle root")
\tout := flag.String("out", "/output/reconcile-report.json", "report path")
\tflag.Parse()

\tids, err := listBundles(*root)
\tif err != nil {{
\t\tfmt.Fprintf(os.Stderr, "list: %v\\n", err)
\t\tos.Exit(1)
\t}}
\tvar rows []emit.Row
\tfor _, id := range ids {{
\t\trow, err := reconcileBundle(*root, id)
\t\tif err != nil {{
\t\t\tfmt.Fprintf(os.Stderr, "%s: %v\\n", id, err)
\t\t\tos.Exit(1)
\t\t}}
\t\trows = append(rows, row)
\t}}
\tif err := emit.Write(*out, rows); err != nil {{
\t\tfmt.Fprintf(os.Stderr, "write: %v\\n", err)
\t\tos.Exit(1)
\t}}
}}

__LIST_BUNDLES__

func reconcileBundle(root, id string) (emit.Row, error) {{
\tmeta, err := descript.LoadMeta(root, id)
\tif err != nil {{
\t\treturn emit.Row{{}}, err
\t}}
\tblobs := map[digest.Digest][]byte{{}}
\tfor _, d := range meta.Manifest {{
\t\tb, err := blob.Load(filepath.Join(root, id), d)
\t\tif err != nil {{
\t\t\treturn emit.Row{{}}, err
\t\t}}
\t\tblobs[d] = b
\t}}
\torder, err := layerwire.BuildStack(meta.Manifest, meta.WireIDs, blobs)
\tif err != nil {{
\t\treturn emit.Row{{}}, err
\t}}
\tvar rawLayers [][]byte
\tvar stacks []string
\tfor _, d := range order {{
\t\tpayload := blobs[d]
\t\traw, err := layerwire.Gunzip(payload)
\t\tif err != nil {{
\t\t\treturn emit.Row{{}}, err
\t\t}}
\t\trawLayers = append(rawLayers, raw)
\t\tstacks = append(stacks, d.String())
\t}}
\tmerged := overlay.ApplyLayers(rawLayers)
\treturn emit.Row{{
\t\tID:     id,
\t\tStacks: stacks,
\t\tPaths:  emit.PathsFromMerged(merged),
\t}}, nil
}}
"""

    packctl_main_broken = packctl_main_body.replace("__LIST_BUNDLES__", list_bundles_broken)
    packctl_main_fixed = packctl_main_body.replace("__LIST_BUNDLES__", list_bundles_fixed)

    w(
        TASK / "environment" / "cmd" / "packctl" / "main.go",
        packctl_main_broken,
    )

    # expose Gunzip from chain
    w(
        TASK / "environment" / "internal" / "layerwire" / "export.go",
        """package layerwire

func Gunzip(b []byte) ([]byte, error) {
\treturn gzipDecompress(b)
}
""",
    )

    w(
        TASK / "environment" / "cmd" / "stackview" / "main.go",
        f"""package main

import (
\t"archive/tar"
\t"bytes"
\t"compress/gzip"
\t"encoding/json"
\t"flag"
\t"fmt"
\t"io"
\t"os"
\t"path/filepath"
\t"sort"

\t"github.com/opencontainers/go-digest"
)

func main() {{
\troot := flag.String("root", "{DATA}", "bundle root")
\tid := flag.String("id", "", "bundle id")
\tflag.Parse()
\tif *id == "" {{
\t\tfmt.Fprintln(os.Stderr, "missing id")
\t\tos.Exit(1)
\t}}
\tbase := filepath.Join(*root, *id)
\tmb, _ := os.ReadFile(filepath.Join(base, "index.json"))
\tvar man struct {{
\t\tLayers []struct {{
\t\t\tDigest digest.Digest `json:"digest"`
\t\t}} `json:"layers"`
\t}}
\t_ = json.Unmarshal(mb, &man)
\tmerged := map[string][]byte{{}}
\tfor _, layer := range man.Layers {{
\t\tpath := filepath.Join(base, "blobs", "sha256", layer.Digest.Encoded())
\t\tb, _ := os.ReadFile(path)
\t\tgr, _ := gzip.NewReader(bytes.NewReader(b))
\t\traw, _ := io.ReadAll(gr)
\t\tgr.Close()
\t\ttr := tar.NewReader(bytes.NewReader(raw))
\t\tfor {{
\t\t\th, err := tr.Next()
\t\t\tif err == io.EOF {{
\t\t\t\tbreak
\t\t\t}}
\t\t\tif h.Typeflag != tar.TypeReg {{
\t\t\t\tcontinue
\t\t\t}}
\t\t\tbody, _ := io.ReadAll(tr)
\t\t\tmerged[h.Name] = body
\t\t}}
\t}}
\tkeys := make([]string, 0, len(merged))
\tfor k := range merged {{
\t\tkeys = append(keys, k)
\t}}
\tsort.Strings(keys)
\tfor _, k := range keys {{
\t\tfmt.Printf("%s\\t%d\\n", k, len(merged[k]))
\t}}
}}
""",
    )

    w(
        TASK / "environment" / "config" / "lab.toml",
        f"""[paths]
root = "{DATA}"
report = "/output/reconcile-report.json"
src = "{LAB}"

[bundles]
ids = {json.dumps(list(BUNDLES))}
""",
    )

    for bid, row in gold.items():
        w(
            TASK / "tests" / "rows" / f"{bid}.json",
            json.dumps(row, indent=2, sort_keys=True) + "\n",
        )

    w(
        TASK / "environment" / "config" / "field-notes.md",
        """# packlab field notes

Bundle trees sit under the configured data root with descriptor JSON and gz tar blobs. Reports emit versioned JSON rows per bundle id.
""",
    )

    w(
        TASK / "environment" / "scripts" / "stackview-wrapper.sh",
        """#!/usr/bin/env bash
exec {LAB}/bin/stackview "$@"
""",
    )

    w(
        TASK / "environment" / "scripts" / "packctl-wrapper.sh",
        """#!/usr/bin/env bash
exec {LAB}/bin/packctl "$@"
""",
    )

    w(
        TASK / "environment" / "data" / "build_fixtures.sh",
        """#!/usr/bin/env bash
set -euo pipefail
# Fixtures are copied from generator output; placeholder for docker build hook.
echo "fixtures pre-seeded"
""",
    )

    # write bundle fixtures
    for bid, spec in specs.items():
        base = TASK / "environment" / "data" / "images" / bid / "blobs" / "sha256"
        for layer in spec.layers:
            wbin(base / layer.digest.removeprefix("sha256:"), layer.gzip_bytes)
        if spec.orphan_digest:
            orphan_path = base / spec.orphan_digest.removeprefix("sha256:")
            if not orphan_path.exists():
                # orphan blob from k9 orphan layer
                orphan = layer_from_specs([TarSpec("orphan/only.txt", "file", b"never-linked\n")])
                wbin(orphan_path, orphan.gzip_bytes)

        wire_ids = [layer.diff_id for layer in spec.layers]
        manifest_layers = []
        for idx in spec.manifest_order:
            layer = spec.layers[idx]
            manifest_layers.append(
                {
                    "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                    "size": len(layer.gzip_bytes),
                    "digest": layer.digest,
                }
            )
        if spec.orphan_digest:
            orphan = layer_from_specs([TarSpec("orphan/only.txt", "file", b"never-linked\n")])
            manifest_layers.append(
                {
                    "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                    "size": len(orphan.gzip_bytes),
                    "digest": orphan.digest,
                }
            )

        wire = {
            "architecture": "amd64",
            "os": "linux",
            "rootfs": {"type": "layers", "diff_ids": wire_ids},
        }
        w(
            TASK / "environment" / "data" / "images" / bid / "wire.json",
            json.dumps(wire, indent=2) + "\n",
        )
        w(
            TASK / "environment" / "data" / "images" / bid / "index.json",
            json.dumps(
                {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "config": {
                        "mediaType": "application/vnd.oci.image.config.v1+json",
                        "size": len(json.dumps(wire)),
                        "digest": "sha256:" + "0" * 64,
                    },
                    "layers": manifest_layers,
                },
                indent=2,
            )
            + "\n",
        )

    w(
        TASK / "environment" / "Dockerfile",
        f"""# syntax=docker/dockerfile:1

FROM {CANONICAL_GOLANG} AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/
RUN go mod tidy \\
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/packctl ./cmd/packctl \\
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/stackview ./cmd/stackview

FROM {CANONICAL_GOLANG}

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends tmux asciinema \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash \\
        ca-certificates \\
        patch=2.7.6-7 \\
        procps \\
        python3=3.11.2-1+b1 \\
        python3-pip=23.0.1+dfsg-1 \\
    && rm -rf /var/lib/apt/lists/*

ENV GOPATH=/go \\
    GOCACHE=/tmp/go-cache \\
    GOMODCACHE=/go/pkg/mod \\
    GOPROXY=off
RUN mkdir -p /go /tmp/go-cache

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=builder --chmod=755 /out/packctl /out/stackview {LAB}/bin/
COPY --from=builder /go/pkg/mod /go/pkg/mod
COPY config/ {LAB}/config/
COPY --chmod=755 scripts/ {LAB}/scripts/
COPY data/images/ {DATA}/
COPY go.mod {LAB}/
COPY cmd/ {LAB}/cmd/
COPY internal/ {LAB}/internal/
COPY pkg/ {LAB}/pkg/
COPY --from=builder /build/go.sum {LAB}/go.sum

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

WORKDIR {LAB}
ENV PATH="{LAB}/bin:${{PATH}}"
""",
    )

    w(
        TASK / "environment" / ".dockerignore",
        """.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
solution/
tests/
""",
    )

    # tests
    # anchor checksums for tamper detection
    anchor_lines: list[str] = []
    for bid in specs:
        blob_dir = TASK / "environment" / "data" / "images" / bid / "blobs" / "sha256"
        for blob_path in sorted(blob_dir.iterdir()):
            if blob_path.is_file():
                anchor_lines.append(f"{sha256_hex(blob_path.read_bytes())}  {bid}/blobs/sha256/{blob_path.name}")
    w(
        TASK / "environment" / "data" / "images" / "anchor.sha256",
        "\n".join(anchor_lines) + "\n",
    )

    staging = TASK / "environment" / "data" / "images" / "bundle-staging"
    staging.mkdir(parents=True, exist_ok=True)
    w(staging / "README.txt", "incomplete staging tree\n")

    w(
        TASK / "tests" / "test.sh",
        """#!/bin/bash

mkdir -p /logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
  --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
""",
    )

    w(
        TASK / "tests" / "test_outputs.py",
        f'''"""Verifier for packlab bundle reconciliation outcomes."""

import json
import subprocess

import pytest
from pathlib import Path

REPORT = Path("/output/reconcile-report.json")
ANCHOR = Path("{DATA}")
ROWS_DIR = Path("/tests/rows")
PACKCTL = Path("{LAB}/bin/packctl")
BUNDLE_IDS = {json.dumps(list(BUNDLES))}


def _expected_bundle(bundle_id: str) -> dict:
    return json.loads((ROWS_DIR / f"{{bundle_id}}.json").read_text(encoding="utf-8"))


def _load_report() -> dict:
    assert REPORT.is_file(), f"missing {{REPORT}}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _by_id(payload: dict) -> dict[str, dict]:
    bundles = payload.get("bundles")
    assert isinstance(bundles, list), payload
    return {{row["id"]: row for row in bundles if isinstance(row, dict) and "id" in row}}


def test_v8_schema_bundle():
    """Report version, bundle ids, and digest prefixes match the lab contract."""
    payload = _load_report()
    assert payload.get("version") == 1
    rows = _by_id(payload)
    for bid in BUNDLE_IDS:
        assert bid in rows, sorted(rows)
        row = rows[bid]
        assert isinstance(row.get("stacks"), list) and row["stacks"]
        assert all(isinstance(d, str) and d.startswith("sha256:") for d in row["stacks"])
        paths = row.get("paths")
        assert isinstance(paths, dict)
        for path, digest in paths.items():
            assert isinstance(path, str) and path
            assert isinstance(digest, str) and digest.startswith("sha256:")


def test_c1_packctl_regenerates_report():
    """The installed packctl CLI reproduces the on-disk reconcile report."""
    tmp = Path("/tmp/packctl-verify-report.json")
    tmp.unlink(missing_ok=True)
    subprocess.run(
        [str(PACKCTL), "--root", str(ANCHOR), "--out", str(tmp)],
        check=True,
        capture_output=True,
        text=True,
    )
    regen = json.loads(tmp.read_text(encoding="utf-8"))
    assert regen == _load_report()


@pytest.mark.parametrize("bundle_id", BUNDLE_IDS)
def test_stacks_match(bundle_id: str):
    """Each bundle stack list matches the expected canonical order."""
    row = _by_id(_load_report())[bundle_id]
    assert row["stacks"] == _expected_bundle(bundle_id)["stacks"]


@pytest.mark.parametrize("bundle_id", BUNDLE_IDS)
def test_paths_match(bundle_id: str):
    """Each bundle path map matches the expected merged view."""
    row = _by_id(_load_report())[bundle_id]
    assert row["paths"] == _expected_bundle(bundle_id)["paths"]


def test_r6_anchor_intact():
    """Bundle blobs under the data root were not rewritten."""
    manifest = ANCHOR / "anchor.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        path = ANCHOR / rel
        assert path.is_file(), rel
        result = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.split()[0] == want_hash, rel
''',
    )

    patch_dir = TASK / "solution" / "patches"
    w(patch_dir / "seq.go", OP_A_GO_FIXED)
    w(patch_dir / "merge.go", RECONCILE_B_GO_FIXED)
    w(patch_dir / "bundle.go", RESOLVE_C_GO_FIXED)
    w(patch_dir / "main.go", packctl_main_fixed)

    patch_pairs = (
        ("seq.go", "internal/layerwire/seq.go", OP_A_GO, OP_A_GO_FIXED),
        ("merge.go", "internal/overlay/merge.go", RECONCILE_B_GO, RECONCILE_B_GO_FIXED),
        ("bundle.go", "internal/descript/bundle.go", RESOLVE_C_GO, RESOLVE_C_GO_FIXED),
        ("main.go", "cmd/packctl/main.go", packctl_main_broken, packctl_main_fixed),
    )
    for name, rel, old, new in patch_pairs:
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
        w(patch_dir / f"{name}.patch", "".join(diff))

    w(
        TASK / "solution" / "solve.sh",
        f"""#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

patch -p1 < "$ROOT_DIR/patches/seq.go.patch"
patch -p1 < "$ROOT_DIR/patches/merge.go.patch"
patch -p1 < "$ROOT_DIR/patches/bundle.go.patch"
patch -p1 < "$ROOT_DIR/patches/main.go.patch"

go build -mod=readonly -trimpath -ldflags="-s -w" -o bin/packctl ./cmd/packctl

mkdir -p /output
rm -f /output/reconcile-report.json
{LAB}/bin/packctl --root {DATA} --out /output/reconcile-report.json

test -s /output/reconcile-report.json
""",
    )

    print(f"Wrote task to {TASK}")
    print("Golden preview:", json.dumps(gold, indent=2)[:500])


if __name__ == "__main__":
    main()
