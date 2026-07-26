#!/usr/bin/env python3
"""Harden landlock-seccomp-notify-admission-mesh after platform EASY + sufficiency FAIL.

Fair seating journal + opaque notify integrity + refresh rematerialize coupling.
Does not clone SoftHSM/signed-plugin fixture trees.
"""
from __future__ import annotations

import json
import pathlib
import textwrap

ROOT = pathlib.Path("/Users/sanyamgupta/Desktop/TERMINUS/tasks/landlock-seccomp-notify-admission-mesh")
ENV = ROOT / "environment"


def w(path: pathlib.Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if mode is not None:
        path.chmod(mode)


def rotl8(x: int, n: int) -> int:
    n %= 8
    return ((x << n) | (x >> (8 - n))) & 0xFF


def derive_material(seed: bytes, epoch: int, lane: int, strand: int) -> bytes:
    epoch_byte = epoch & 0xFF
    out = bytearray()
    for i, b in enumerate(seed):
        mix = rotl8(epoch_byte, (i % 5) + 1)
        stride = (5 * i + 1) & 0xFF
        out.append(b ^ mix ^ stride ^ strand ^ lane)
    return bytes(out)


def keyed_fold(payload: bytes, material: bytes) -> int:
    total = 0
    for i, p in enumerate(payload):
        total = (total + (p ^ material[i % len(material)])) & 0xFF
    return total


def main() -> None:
    seed = bytes.fromhex("a1b2c3d4e5f60718293a4b5c6d7e8f90")
    strand = 0x3D  # 61
    # lane ids per job family
    lanes = {
        "m2": 1,
        "w2": 1,
        "k9": 2,
        "n4": 2,
        "p7": 3,
        "q3": 3,
        "r6": 4,
        "t1": 4,
        "u8": 5,
        "v5": 5,
        "x2": 1,
        "h4": 2,
        "s9": 3,  # replay cell
    }

    # --- seating journal (agent-visible authority) ---
    journal_lines = [
        {"alias": "/data/alias/m2/blob", "canon": "/data/vault/m2/blob"},
        {"alias": "/data/alias/w2/blob", "canon": "/data/vault/w2/blob"},
        {"alias": "/data/alias/k9/blob", "canon": "/data/outside/k9/blob"},
        {"alias": "/data/alias/v5/blob", "via": "/data/bridge/v5/blob"},
        {"alias": "/data/bridge/v5/blob", "canon": "/data/vault/v5/blob"},
    ]
    w(
        ENV / "data/seating/canon.journal",
        "".join(json.dumps(x, separators=(",", ":")) + "\n" for x in journal_lines),
    )

    # Incomplete/wrong durable.map (live decoy shape)
    w(
        ENV / "data/roots/durable.map",
        textwrap.dedent(
            """\
            # durable seating seed (stale / incomplete after mesh churn)
            /data/alias/m2/blob=/data/outside/m2/blob
            /data/alias/w2/blob=/data/outside/w2/blob
            /data/alias/k9/blob=/data/vault/k9/blob
            /data/alias/v5/blob=/data/outside/v5/blob
            """
        ),
    )
    w(
        ENV / "data/roots/live.map",
        textwrap.dedent(
            """\
            # live post-refresh decoys (single-hop looks finished)
            /data/alias/m2/blob=/data/outside/m2/blob
            /data/alias/w2/blob=/data/outside/w2/blob
            /data/alias/k9/blob=/data/vault/k9/blob
            /data/alias/v5/blob=/data/outside/v5/blob
            /data/bridge/v5/blob=/data/vault/v5/blob
            """
        ),
    )

    # Surface bait
    w(ENV / "data/surface/allow.list", "/data/\n")
    w(
        ENV / "data/surface/binder.toml",
        'mode = "live"\nallow = "/data/"\n',
    )
    w(
        ENV / "data/revoke/window.toml",
        'lo = 0\nhi = 99\nmarks = ["job-q3", "job-r6"]\n',
    )
    w(ENV / "data/w1/allow.list", "/data/vault/\n")
    w(ENV / "data/state/runtime.json", '{"epoch": 7}\n')
    w(
        ENV / "ops/trust_policy.toml",
        textwrap.dedent(
            """\
            # Deep admission policy (surface probes ignore this sheet).
            [trust]
            authority = "durable"
            verification = "keyed"
            replay_protection = "monotonic"

            [weave]
            strand = 61
            """
        ),
    )
    w(
        ENV / "data/fixtures/seed.json",
        json.dumps({"seed_hex": seed.hex(), "preserve": True}, indent=2) + "\n",
    )

    # Scenarios + notify frames
    scenarios = [
        # id, job, req, op, wire, fd_epoch, claim, epoch_for_frame, payload, note
        ("m2", "job-m2", "/data/alias/m2/blob", "open", "pass", 8, 0, 10, b"open-m2", "admit"),
        ("w2", "job-w2", "/data/alias/w2/blob", "open", "pass", 8, 0, 10, b"open-w2", "admit"),
        ("k9", "job-k9", "/data/alias/k9/blob", "open", "pass", 8, 0, 10, b"open-k9", "path_drift"),
        ("n4", "job-n4", "/data/vault/n4/blob", "open", "pass", 3, 0, 10, b"open-n4", "fd_stale"),
        ("p7", "job-p7", "/data/vault/p7/blob", "exec", "hold", 8, 0, 10, b"exec-p7", "notify_skew"),
        ("q3", "job-q3", "/data/vault/q3/blob", "open", "pass", 8, 5, 10, b"open-q3", "epoch_revoke"),
        ("r6", "job-r6", "/data/vault/r6/blob", "open", "pass", 8, 2, 10, b"open-r6", "admit"),
        ("t1", "job-t1", "/data/vault/t1/blob", "exec", "pass", 8, 0, 10, b"exec-t1", "admit"),
        ("u8", "job-u8", "/data/vault/u8/blob", "open", "hold", 8, 0, 10, b"open-u8", "admit"),
        ("v5", "job-v5", "/data/alias/v5/blob", "open", "pass", 8, 0, 10, b"open-v5", "admit"),
        ("x2", "job-x2", "/data/vault/x2/blob", "open", "pass", 7, 0, 10, b"open-x2", "admit"),
        ("h4", "job-h4", "/data/alias/k9/blob", "exec", "hold", 8, 0, 10, b"exec-h4", "path_drift"),
        # replay: same lane stream as p7 epoch 10, non-advancing ts
        ("s9", "job-s9", "/data/vault/s9/blob", "open", "pass", 8, 0, 10, b"open-s9", "replay"),
    ]

    # Build notify credential JSONL (epoch,lane,ts,payload_hex,check)
    # Stream order for lane 3 (p7 then s9): ts must advance; s9 uses same/lower ts → replay
    cred_rows = []
    audit_rows = []
    for sid, job, req, op, wire, fd_epoch, claim, ep, payload, note in scenarios:
        lane = lanes[sid]
        mat = derive_material(seed, ep, lane, strand)
        check = keyed_fold(payload, mat)
        # timestamps: p7 gets 100, s9 gets 100 (replay), others unique advancing
        if sid == "p7":
            ts = 100
        elif sid == "s9":
            ts = 100  # non-advancing on lane 3
        else:
            ts = 50 + ord(sid[0])
        row = {
            "id": sid,
            "job_id": job,
            "epoch": ep,
            "lane": lane,
            "ts": ts,
            "payload_hex": payload.hex(),
            "check": check,
            "status": "active",
        }
        # trap: legacy-signed integrity for one inject sample in fixtures only
        cred_rows.append(row)
        if note in ("admit", "notify_skew", "path_drift") and sid in ("m2", "p7", "k9", "v5", "t1"):
            audit_rows.append(
                {
                    "seed_hex": seed.hex(),
                    "epoch": ep,
                    "lane": lane,
                    "payload_hex": payload.hex(),
                    "check": check,
                }
            )

        scen = {
            "id": sid,
            "job_id": job,
            "req": req,
            "op": op,
            "wire": wire,
            "fd_epoch": fd_epoch,
            "claim": claim,
            "epoch": ep,
            "lane": lane,
            "ts": ts,
            "payload_hex": payload.hex(),
            "check": check,
        }
        w(ENV / f"data/scenarios/{sid}.json", json.dumps(scen, separators=(",", ":")) + "\n")

    w(
        ENV / "data/credentials/notify.jsonl",
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in cred_rows),
    )

    # Legacy-schedule trap frames for integrity discovery contrast
    legacy_checks = []
    for ar in audit_rows[:2]:
        # wrong: seed^epoch^i plain
        ep = ar["epoch"]
        payload = bytes.fromhex(ar["payload_hex"])
        legacy_mat = bytes(b ^ (ep & 0xFF) ^ i for i, b in enumerate(seed))
        legacy_check = keyed_fold(payload, legacy_mat)
        legacy_checks.append(
            {
                "epoch": ep,
                "lane": ar["lane"],
                "payload_hex": ar["payload_hex"],
                "check": legacy_check,
                "note": "prior_schedule",
            }
        )
    w(
        ENV / "data/fixtures/pre_incident_audit.log",
        "# pre-incident verifier samples (seed/payload/check; material not exported)\n"
        + "".join(json.dumps(x, separators=(",", ":")) + "\n" for x in audit_rows)
        + "# prior-schedule traps (must integrity_failure under deep rules)\n"
        + "".join(json.dumps(x, separators=(",", ":")) + "\n" for x in legacy_checks),
    )
    w(
        ENV / "data/fixtures/surface_attestation.json",
        json.dumps({"status": "ok", "accepted": len(scenarios), "path": "surface"}, indent=2)
        + "\n",
    )

    # Preference sheets (broken)
    w(
        ENV / "qx/internal/seat_k.go",
        textwrap.dedent(
            """\
            package internal

            var SeatMode = "live"

            var SeatAllow = "/data/"
            """
        ),
    )
    w(
        ENV / "qx/internal/band_k.go",
        textwrap.dedent(
            """\
            package internal

            var BandLo int64 = 0

            var BandHi int64 = 99
            """
        ),
    )
    # Broken binder: live map + surface allow; ignores journal
    w(
        ENV / "qx/internal/bind_y.go",
        textwrap.dedent(
            """\
            package internal

            func bind_y(dir string, lst string) (mapPath string, allowPath string, allowInline string, useJournal bool) {
            	_ = lst
            	_ = SeatMode
            	_ = SeatAllow
            	return dir + "/live.map", "/app/data/surface/allow.list", "", false
            }
            """
        ),
    )

    # fold_a: multi-hop; journal when useJournal
    w(
        ENV / "qx/internal/fold_a.go",
        textwrap.dedent(
            """\
            package internal

            import "strings"

            type rowA struct {
            	Req     string
            	Dir     string
            	Lst     string
            	Journal string
            }

            type slotA struct {
            	Canon string
            	Bit   int
            }

            func fold_a(a rowA, b *slotA) error {
            	mapPath, allowPath, allowInline, useJournal := bind_y(a.Dir, a.Lst)
            	m, err := loadMap(mapPath)
            	if err != nil {
            		return err
            	}
            	if useJournal {
            		jm, err := loadJournal(a.Journal)
            		if err != nil {
            			return err
            		}
            		for k, v := range jm {
            			m[k] = v
            		}
            	}
            	canon := a.Req
            	for i := 0; i < 8; i++ {
            		v, ok := m[canon]
            		if !ok || v == canon {
            			break
            		}
            		canon = v
            	}
            	b.Canon = canon
            	b.Bit = 0

            	var allows []string
            	if allowInline != "" {
            		allows = []string{allowInline}
            	} else {
            		allows, err = loadList(allowPath)
            		if err != nil {
            			return err
            		}
            	}
            	best := 0
            	for _, pref := range allows {
            		if strings.HasPrefix(canon, pref) && len(pref) > best {
            			best = len(pref)
            			b.Bit = 1
            		}
            	}
            	return nil
            }
            """
        ),
    )

    # emit_c: correct rules + integrity + replay inputs from row
    w(
        ENV / "qx/internal/emit_c.go",
        textwrap.dedent(
            """\
            package internal

            type rowC struct {
            	ID      string
            	Tok     string
            	Bit     int
            	Nok     int
            	Integ   int
            	Replay  int
            	FdEpoch int64
            	Claim   int64
            	RunPath string
            	WinPath string
            }

            type slotC struct {
            	Decision string
            	Reason   string
            	Reloaded int64
            }

            func emit_c(a rowC, b *slotC) error {
            	ep, err := readEpoch(a.RunPath)
            	if err != nil {
            		return err
            	}
            	_, _, marks, err := readWindow(a.WinPath)
            	if err != nil {
            		return err
            	}

            	b.Reloaded = ep

            	if a.FdEpoch < ep {
            		b.Decision = "quarantine"
            		b.Reason = "fd_stale"
            		return nil
            	}

            	marked := false
            	for _, m := range marks {
            		if m == a.Tok {
            			marked = true
            			break
            		}
            	}
            	if marked && a.Claim >= BandLo && a.Claim <= BandHi {
            		b.Decision = "quarantine"
            		b.Reason = "epoch_revoke"
            		return nil
            	}

            	if a.Integ == 0 {
            		b.Decision = "quarantine"
            		b.Reason = "integrity_failure"
            		return nil
            	}
            	if a.Replay == 1 {
            		b.Decision = "quarantine"
            		b.Reason = "replay"
            		return nil
            	}

            	if a.Bit == 0 {
            		b.Decision = "quarantine"
            		b.Reason = "path_drift"
            		return nil
            	}
            	if a.Nok == 0 {
            		b.Decision = "quarantine"
            		b.Reason = "notify_skew"
            		return nil
            	}

            	b.Decision = "accept"
            	b.Reason = "ok_admit"
            	return nil
            }
            """
        ),
    )

    # sieve_b: correct notify wire; also integrity path in rz_main
    w(
        ENV / "rz/sieve_b.c",
        textwrap.dedent(
            """\
            #include <string.h>

            #include "sieve_b.h"

            int sieve_b(int a, const char *b, const char *c)
            {
                if (a == 0) {
                    return 0;
                }
                if (b == NULL || b[0] == '\\0') {
                    return 0;
                }
                if (strcmp(b, "open") == 0) {
                    return 1;
                }
                if (strcmp(b, "exec") == 0) {
                    if (c != NULL && strcmp(c, "hold") == 0) {
                        return 0;
                    }
                    if (c != NULL && strcmp(c, "pass") == 0) {
                        return 1;
                    }
                    return 0;
                }
                return 0;
            }
            """
        ),
    )

    # Broken integrity: plain-sum (surface schedule) — in knit_m.c
    w(
        ENV / "rz/knit_m.c",
        textwrap.dedent(
            """\
            #include <stdio.h>
            #include <stdlib.h>
            #include <string.h>

            #include "knit_m.h"

            /* Broken: plain payload sum — ignores material schedule. */
            int knit_m(const unsigned char *payload, size_t n,
                       const unsigned char *material, size_t mlen,
                       unsigned expect)
            {
                unsigned sum = 0;
                size_t i;
                (void)material;
                (void)mlen;
                for (i = 0; i < n; i++) {
                    sum = (sum + payload[i]) & 0xffu;
                }
                return sum == (expect & 0xffu);
            }
            """
        ),
    )
    w(
        ENV / "rz/knit_m.h",
        textwrap.dedent(
            """\
            #ifndef KNIT_M_H
            #define KNIT_M_H

            #include <stddef.h>

            int knit_m(const unsigned char *payload, size_t n,
                       const unsigned char *material, size_t mlen,
                       unsigned expect);

            #endif
            """
        ),
    )

    # Material derive helper (broken: seed^epoch^i)
    w(
        ENV / "rz/mat_q.c",
        textwrap.dedent(
            """\
            #include <stdint.h>
            #include <string.h>

            #include "mat_q.h"

            /* Broken legacy schedule: seed[i] ^ epoch_lo ^ i */
            void mat_q(const unsigned char *seed, size_t n, unsigned epoch,
                       unsigned lane, unsigned strand, unsigned char *out)
            {
                size_t i;
                unsigned char elo = (unsigned char)(epoch & 0xffu);
                (void)lane;
                (void)strand;
                for (i = 0; i < n; i++) {
                    out[i] = (unsigned char)(seed[i] ^ elo ^ (unsigned char)i);
                }
            }
            """
        ),
    )
    w(
        ENV / "rz/mat_q.h",
        textwrap.dedent(
            """\
            #ifndef MAT_Q_H
            #define MAT_Q_H

            #include <stddef.h>

            void mat_q(const unsigned char *seed, size_t n, unsigned epoch,
                       unsigned lane, unsigned strand, unsigned char *out);

            #endif
            """
        ),
    )

    # rz_main: decide + integ commands
    w(
        ENV / "rz/rz_main.c",
        textwrap.dedent(
            """\
            #include <stdio.h>
            #include <stdlib.h>
            #include <string.h>

            #include "knit_m.h"
            #include "mat_q.h"
            #include "sieve_b.h"
            #include "skim_sieve.h"
            #include "wire.h"

            static int hex_nibble(char c)
            {
                if (c >= '0' && c <= '9') return c - '0';
                if (c >= 'a' && c <= 'f') return c - 'a' + 10;
                if (c >= 'A' && c <= 'F') return c - 'A' + 10;
                return -1;
            }

            static int parse_hex(const char *s, unsigned char *out, size_t cap, size_t *n)
            {
                size_t len = strlen(s);
                size_t i;
                if (len % 2 != 0 || len / 2 > cap) return -1;
                for (i = 0; i < len; i += 2) {
                    int hi = hex_nibble(s[i]);
                    int lo = hex_nibble(s[i + 1]);
                    if (hi < 0 || lo < 0) return -1;
                    out[i / 2] = (unsigned char)((hi << 4) | lo);
                }
                *n = len / 2;
                return 0;
            }

            static void usage(const char *prog)
            {
                fprintf(stderr, "usage: %s decide <bit> <op> <wire>\\n", prog);
                fprintf(stderr, "       %s surface <bit> <op> <wire>\\n", prog);
                fprintf(stderr, "       %s integ <seed_hex> <epoch> <lane> <strand> <payload_hex> <check>\\n", prog);
            }

            int main(int argc, char **argv)
            {
                int bit;
                int out;

                if (argc >= 2 && strcmp(argv[1], "integ") == 0) {
                    unsigned char seed[64];
                    unsigned char payload[256];
                    unsigned char material[64];
                    size_t sn = 0, pn = 0;
                    unsigned epoch, lane, strand, check;
                    if (argc != 8) {
                        usage(argv[0]);
                        return 2;
                    }
                    if (parse_hex(argv[2], seed, sizeof seed, &sn) != 0) return 2;
                    epoch = (unsigned)strtoul(argv[3], NULL, 10);
                    lane = (unsigned)strtoul(argv[4], NULL, 10);
                    strand = (unsigned)strtoul(argv[5], NULL, 10);
                    if (parse_hex(argv[6], payload, sizeof payload, &pn) != 0) return 2;
                    check = (unsigned)strtoul(argv[7], NULL, 10);
                    mat_q(seed, sn, epoch, lane, strand, material);
                    out = knit_m(payload, pn, material, sn, check);
                    printf("%d\\n", out);
                    return WIRE_OK;
                }

                if (argc != 5) {
                    usage(argv[0]);
                    return 2;
                }

                bit = atoi(argv[2]);
                if (strcmp(argv[1], "surface") == 0) {
                    out = skim_sieve(bit, argv[3], argv[4]);
                } else if (strcmp(argv[1], "decide") == 0) {
                    out = sieve_b(bit, argv[3], argv[4]);
                } else {
                    usage(argv[0]);
                    return 2;
                }

                printf("%d\\n", out);
                return WIRE_OK;
            }
            """
        ),
    )

    # Extend io_util with journal loader + keep existing helpers
    w(
        ENV / "qx/internal/io_util.go",
        textwrap.dedent(
            '''\
            package internal

            import (
            	"bufio"
            	"encoding/json"
            	"os"
            	"path/filepath"
            	"sort"
            	"strconv"
            	"strings"
            )

            type scen struct {
            	ID         string `json:"id"`
            	JobID      string `json:"job_id"`
            	Req        string `json:"req"`
            	Op         string `json:"op"`
            	Wire       string `json:"wire"`
            	FdEpoch    int64  `json:"fd_epoch"`
            	Claim      int64  `json:"claim"`
            	Epoch      int64  `json:"epoch"`
            	Lane       int    `json:"lane"`
            	Ts         int64  `json:"ts"`
            	PayloadHex string `json:"payload_hex"`
            	Check      int    `json:"check"`
            }

            func LoadScenarios(dir string) ([]scen, error) {
            	entries, err := os.ReadDir(dir)
            	if err != nil {
            		return nil, err
            	}
            	var out []scen
            	for _, e := range entries {
            		if e.IsDir() || !stringsHasSuffix(e.Name(), ".json") {
            			continue
            		}
            		raw, err := os.ReadFile(filepath.Join(dir, e.Name()))
            		if err != nil {
            			return nil, err
            		}
            		var s scen
            		if err := json.Unmarshal(raw, &s); err != nil {
            			return nil, err
            		}
            		out = append(out, s)
            	}
            	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
            	return out, nil
            }

            func stringsHasSuffix(s, suf string) bool {
            	return len(s) >= len(suf) && s[len(s)-len(suf):] == suf
            }

            func loadMap(src string) (map[string]string, error) {
            	f, err := os.Open(src)
            	if err != nil {
            		return nil, err
            	}
            	defer f.Close()
            	out := make(map[string]string)
            	sc := bufio.NewScanner(f)
            	for sc.Scan() {
            		line := strings.TrimSpace(sc.Text())
            		if line == "" || strings.HasPrefix(line, "#") {
            			continue
            		}
            		parts := strings.SplitN(line, "=", 2)
            		if len(parts) != 2 {
            			continue
            		}
            		out[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
            	}
            	return out, sc.Err()
            }

            func loadJournal(src string) (map[string]string, error) {
            	raw, err := os.ReadFile(src)
            	if err != nil {
            		return nil, err
            	}
            	out := make(map[string]string)
            	for _, line := range strings.Split(string(raw), "\\n") {
            		line = strings.TrimSpace(line)
            		if line == "" || strings.HasPrefix(line, "#") {
            			continue
            		}
            		var row map[string]string
            		if err := json.Unmarshal([]byte(line), &row); err != nil {
            			continue
            		}
            		alias := row["alias"]
            		if alias == "" {
            			continue
            		}
            		if c := row["canon"]; c != "" {
            			out[alias] = c
            		} else if v := row["via"]; v != "" {
            			out[alias] = v
            		}
            	}
            	return out, nil
            }

            func loadList(src string) ([]string, error) {
            	raw, err := os.ReadFile(src)
            	if err != nil {
            		return nil, err
            	}
            	var out []string
            	for _, line := range strings.Split(string(raw), "\\n") {
            		line = strings.TrimSpace(line)
            		if line == "" || strings.HasPrefix(line, "#") {
            			continue
            		}
            		out = append(out, line)
            	}
            	return out, nil
            }

            func readEpoch(src string) (int64, error) {
            	raw, err := os.ReadFile(src)
            	if err != nil {
            		return 0, err
            	}
            	s := strings.TrimSpace(string(raw))
            	idx := strings.Index(s, "\\"epoch\\"")
            	if idx < 0 {
            		return 0, os.ErrInvalid
            	}
            	rest := s[idx:]
            	colon := strings.Index(rest, ":")
            	if colon < 0 {
            		return 0, os.ErrInvalid
            	}
            	num := strings.TrimSpace(rest[colon+1:])
            	num = strings.TrimRight(num, "}\\n\\r\\t ,")
            	return strconv.ParseInt(num, 10, 64)
            }

            func readWindow(src string) (int64, int64, []string, error) {
            	raw, err := os.ReadFile(src)
            	if err != nil {
            		return 0, 0, nil, err
            	}
            	var lo, hi int64
            	var marks []string
            	for _, line := range strings.Split(string(raw), "\\n") {
            		line = strings.TrimSpace(line)
            		if strings.HasPrefix(line, "lo") {
            			parts := strings.SplitN(line, "=", 2)
            			if len(parts) == 2 {
            				lo, _ = strconv.ParseInt(strings.TrimSpace(parts[1]), 10, 64)
            			}
            		} else if strings.HasPrefix(line, "hi") {
            			parts := strings.SplitN(line, "=", 2)
            			if len(parts) == 2 {
            				hi, _ = strconv.ParseInt(strings.TrimSpace(parts[1]), 10, 64)
            			}
            		} else if strings.HasPrefix(line, "marks") {
            			parts := strings.SplitN(line, "=", 2)
            			if len(parts) == 2 {
            				inner := strings.TrimSpace(parts[1])
            				inner = strings.TrimPrefix(inner, "[")
            				inner = strings.TrimSuffix(inner, "]")
            				for _, tok := range strings.Split(inner, ",") {
            					tok = strings.TrimSpace(tok)
            					tok = strings.Trim(tok, "\\"'")
            					if tok != "" {
            						marks = append(marks, tok)
            					}
            				}
            			}
            		}
            	}
            	return lo, hi, marks, nil
            }

            func loadStrand(path string) int {
            	raw, err := os.ReadFile(path)
            	if err != nil {
            		return 0
            	}
            	for _, line := range strings.Split(string(raw), "\\n") {
            		line = strings.TrimSpace(line)
            		if strings.HasPrefix(line, "strand") {
            			parts := strings.SplitN(line, "=", 2)
            			if len(parts) == 2 {
            				v := strings.TrimSpace(parts[1])
            				v = strings.Trim(v, "\\"")
            				n, _ := strconv.Atoi(v)
            				return n
            			}
            		}
            	}
            	return 0
            }

            func loadSeedHex(path string) (string, error) {
            	raw, err := os.ReadFile(path)
            	if err != nil {
            		return "", err
            	}
            	var obj map[string]any
            	if err := json.Unmarshal(raw, &obj); err != nil {
            		return "", err
            	}
            	if s, ok := obj["seed_hex"].(string); ok {
            		return s, nil
            	}
            	return "", os.ErrInvalid
            }
            '''
        ),
    )

    # run.go with integrity + replay tracking
    w(
        ENV / "qx/internal/run.go",
        textwrap.dedent(
            '''\
            package internal

            import (
            	"encoding/json"
            	"fmt"
            	"os"
            	"os/exec"
            	"sort"
            	"strconv"
            	"strings"
            )

            type caseRow struct {
            	ID         string `json:"id"`
            	JobID      string `json:"job_id"`
            	Decision   string `json:"decision"`
            	ReasonCode string `json:"reason_code"`
            }

            type ledger struct {
            	SchemaVersion string    `json:"schema_version"`
            	Cases         []caseRow `json:"cases"`
            	ReloadEpoch   int64     `json:"reload_epoch"`
            }

            type qRow struct {
            	Epoch  int64  `json:"epoch"`
            	Lane   int    `json:"lane"`
            	Ts     int64  `json:"ts"`
            	Reason string `json:"reason"`
            }

            type quarantine struct {
            	Version int    `json:"version"`
            	Rows    []qRow `json:"rows"`
            }

            // RunAll walks scenarios and writes output artifacts.
            func RunAll(root string) error {
            	scens, err := LoadScenarios(root + "/data/scenarios")
            	if err != nil {
            		return err
            	}
            	seedHex, err := loadSeedHex(root + "/data/fixtures/seed.json")
            	if err != nil {
            		return err
            	}
            	strand := loadStrand(root + "/ops/trust_policy.toml")

            	// Capture-order replay tracking per epoch|lane across scenarios sorted by id then ts.
            	ordered := append([]scen(nil), scens...)
            	sort.SliceStable(ordered, func(i, j int) bool {
            		if ordered[i].Epoch == ordered[j].Epoch && ordered[i].Lane == ordered[j].Lane {
            			if ordered[i].Ts == ordered[j].Ts {
            				return ordered[i].ID < ordered[j].ID
            			}
            			return ordered[i].Ts < ordered[j].Ts
            		}
            		if ordered[i].Epoch == ordered[j].Epoch {
            			return ordered[i].Lane < ordered[j].Lane
            		}
            		return ordered[i].Epoch < ordered[j].Epoch
            	})
            	lastTS := map[string]int64{}
            	replayHit := map[string]bool{}
            	for _, s := range ordered {
            		key := fmt.Sprintf("%d|%d", s.Epoch, s.Lane)
            		if prev, ok := lastTS[key]; ok && s.Ts <= prev {
            			replayHit[s.ID] = true
            		} else {
            			lastTS[key] = s.Ts
            		}
            	}

            	var cases []caseRow
            	var qrows []qRow
            	var reload int64
            	for _, s := range scens {
            		var sa slotA
            		ra := rowA{
            			Req:     s.Req,
            			Dir:     root + "/data/roots",
            			Lst:     root + "/data/w1/allow.list",
            			Journal: root + "/data/seating/canon.journal",
            		}
            		if err := fold_a(ra, &sa); err != nil {
            			return fmt.Errorf("fold: %w", err)
            		}

            		nok, err := runHelper(root+"/bin/nhelper", sa.Bit, s.Op, s.Wire)
            		if err != nil {
            			return fmt.Errorf("helper: %w", err)
            		}

            		integ, err := runInteg(root+"/bin/nhelper", seedHex, s.Epoch, s.Lane, strand, s.PayloadHex, s.Check)
            		if err != nil {
            			return fmt.Errorf("integ: %w", err)
            		}
            		rep := 0
            		if replayHit[s.ID] {
            			rep = 1
            		}

            		var sc slotC
            		rc := rowC{
            			ID:      s.ID,
            			Tok:     s.JobID,
            			Bit:     sa.Bit,
            			Nok:     nok,
            			Integ:   integ,
            			Replay:  rep,
            			FdEpoch: s.FdEpoch,
            			Claim:   s.Claim,
            			RunPath: root + "/data/state/runtime.json",
            			WinPath: root + "/data/revoke/window.toml",
            		}
            		if err := emit_c(rc, &sc); err != nil {
            			return fmt.Errorf("emit: %w", err)
            		}
            		reload = sc.Reloaded
            		cases = append(cases, caseRow{
            			ID:         s.ID,
            			JobID:      s.JobID,
            			Decision:   sc.Decision,
            			ReasonCode: sc.Reason,
            		})
            		if sc.Decision == "quarantine" {
            			qrows = append(qrows, qRow{
            				Epoch:  s.Epoch,
            				Lane:   s.Lane,
            				Ts:     s.Ts,
            				Reason: sc.Reason,
            			})
            		}
            	}

            	out := ledger{
            		SchemaVersion: "admit-mesh-1",
            		Cases:         cases,
            		ReloadEpoch:   reload,
            	}
            	raw, err := json.MarshalIndent(out, "", "  ")
            	if err != nil {
            		return err
            	}
            	if err := os.MkdirAll("/output", 0o755); err != nil {
            		return err
            	}
            	if err := os.WriteFile("/output/admit-ledger.json", append(raw, '\\n'), 0o644); err != nil {
            		return err
            	}
            	q := quarantine{Version: 1, Rows: qrows}
            	qraw, err := json.MarshalIndent(q, "", "  ")
            	if err != nil {
            		return err
            	}
            	return os.WriteFile("/output/quarantine.json", append(qraw, '\\n'), 0o644)
            }

            func runHelper(bin string, bit int, op, wire string) (int, error) {
            	cmd := exec.Command(bin, "decide", strconv.Itoa(bit), op, wire)
            	out, err := cmd.Output()
            	if err != nil {
            		return 0, err
            	}
            	return strconv.Atoi(strings.TrimSpace(string(out)))
            }

            func runInteg(bin, seedHex string, epoch int64, lane, strand int, payloadHex string, check int) (int, error) {
            	cmd := exec.Command(
            		bin, "integ", seedHex,
            		strconv.FormatInt(epoch, 10),
            		strconv.Itoa(lane),
            		strconv.Itoa(strand),
            		payloadHex,
            		strconv.Itoa(check),
            	)
            	out, err := cmd.Output()
            	if err != nil {
            		return 0, err
            	}
            	return strconv.Atoi(strings.TrimSpace(string(out)))
            }

            func SurfLine(req string) string {
            	if skim_fold(req) == 1 {
            		return "OK"
            	}
            	return "FAIL"
            }
            '''
        ),
    )

    print("core files written; continuing in part 2...")
    # Write EXPECTED for tests into a sidecar the generator also emits
    expected = {
        "m2": ("job-m2", "accept", "ok_admit"),
        "w2": ("job-w2", "accept", "ok_admit"),
        "k9": ("job-k9", "quarantine", "path_drift"),
        "n4": ("job-n4", "quarantine", "fd_stale"),
        "p7": ("job-p7", "quarantine", "notify_skew"),
        "q3": ("job-q3", "quarantine", "epoch_revoke"),
        "r6": ("job-r6", "accept", "ok_admit"),
        "t1": ("job-t1", "accept", "ok_admit"),
        "u8": ("job-u8", "accept", "ok_admit"),
        "v5": ("job-v5", "accept", "ok_admit"),
        "x2": ("job-x2", "accept", "ok_admit"),
        "h4": ("job-h4", "quarantine", "path_drift"),
        "s9": ("job-s9", "quarantine", "replay"),
    }
    w(ROOT / ".gen_expected.json", json.dumps(expected, indent=2) + "\n")
    print("EXPECTED:", expected)


if __name__ == "__main__":
    main()
