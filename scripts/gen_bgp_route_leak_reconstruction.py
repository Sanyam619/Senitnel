#!/usr/bin/env python3
"""Generate tasks/bgp-route-leak-reconstruction (authoring tool, not shipped)."""
from __future__ import annotations

import ipaddress
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "bgp-route-leak-reconstruction"
ENV = TASK / "environment"
TASK_ROOT = "/opt/bgplab"
OUTPUT_ROOT = "/output"

LOCAL_AS = 65000
ROUTER_ID = "10.0.0.1"


@dataclass
class Route:
    prefix: str
    peer: str
    peer_as: int
    peer_addr: str
    next_hop: str
    as_path: list[int]
    local_pref: int
    med: int
    origin: str  # igp, egp, incomplete


@dataclass
class Policy:
    local_as: int
    router_id: str
    always_compare_med: bool = False


def w(rel: str, content: str) -> None:
    p = TASK / rel if not rel.startswith("environment/") else ENV / rel.removeprefix("environment/")
    p.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(content).lstrip("\n")
    text = text.replace("{TASK_ROOT}", TASK_ROOT).replace("{OUTPUT_ROOT}", OUTPUT_ROOT)
    p.write_text(text, encoding="utf-8")


def origin_rank(o: str) -> int:
    return {"igp": 0, "egp": 1, "incomplete": 2}.get(o, 3)


def neighbor_as(route: Route) -> int:
    return route.as_path[0] if route.as_path else route.peer_as


def has_loop(route: Route, local_as: int) -> bool:
    return local_as in route.as_path


def med_comparable(a: Route, b: Route, pol: Policy) -> bool:
    if pol.always_compare_med:
        return True
    return neighbor_as(a) == neighbor_as(b)


def compare_routes(a: Route, b: Route, pol: Policy) -> int:
    """Return positive if a is better than b."""
    if a.local_pref != b.local_pref:
        return a.local_pref - b.local_pref
    if len(a.as_path) != len(b.as_path):
        return len(b.as_path) - len(a.as_path)
    oa, ob = origin_rank(a.origin), origin_rank(b.origin)
    if oa != ob:
        return ob - oa
    if med_comparable(a, b, pol) and a.med != b.med:
        return b.med - a.med
    if a.peer_addr != b.peer_addr:
        return 1 if a.peer_addr < b.peer_addr else -1
    return 0


def best_path(routes: list[Route], pol: Policy, *, naive: bool) -> Route | None:
    candidates = routes
    if not naive:
        candidates = [r for r in routes if not has_loop(r, pol.local_as)]
    if not candidates:
        return None
    best = candidates[0]
    for r in candidates[1:]:
        if naive:
            # naive: always compare MED, skip loop filter already skipped above for naive
            better = False
            if r.local_pref > best.local_pref:
                better = True
            elif r.local_pref == best.local_pref:
                if len(r.as_path) < len(best.as_path):
                    better = True
                elif len(r.as_path) == len(best.as_path):
                    if origin_rank(r.origin) < origin_rank(best.origin):
                        better = True
                    elif origin_rank(r.origin) == origin_rank(best.origin):
                        if r.med < best.med:
                            better = True
                        elif r.med == best.med and r.peer_addr < best.peer_addr:
                            better = True
        else:
            better = compare_routes(r, best, pol) > 0
        if better:
            best = r
    return best


SCENARIOS: dict[str, list[Route]] = {
    "alpha": [
        Route("10.1.0.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65010], 200, 0, "igp"),
        Route("10.1.0.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65010], 150, 0, "igp"),
        Route("10.1.1.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65020, 65010], 100, 0, "igp"),
        Route("10.1.1.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65010], 100, 0, "igp"),
        Route("10.1.2.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65011], 100, 0, "igp"),
        Route("10.1.2.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65011], 100, 0, "egp"),
        Route("10.1.3.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65012], 100, 0, "igp"),
        Route("10.1.3.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65012], 150, 0, "igp"),
    ],
    "bravo": [
        Route("10.2.0.0/24", "peer_c", 65300, "192.0.2.30", "192.0.2.30", [65300, 65030], 100, 50, "igp"),
        Route("10.2.0.0/24", "peer_c", 65300, "192.0.2.30", "192.0.2.30", [65300, 65100], 100, 10, "igp"),
        Route("10.2.1.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65031], 100, 5, "igp"),
        Route("10.2.1.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65200], 100, 1, "igp"),
    ],
    "charlie": [
        Route("10.3.0.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, LOCAL_AS, 65040], 200, 0, "igp"),
        Route("10.3.0.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65040], 100, 0, "igp"),
        Route("10.3.1.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65041], 100, 0, "igp"),
        Route("10.3.1.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65041], 100, 0, "igp"),
        Route("10.3.2.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65042], 150, 0, "igp"),
        Route("10.3.2.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65042], 100, 0, "igp"),
    ],
    "delta": [
        Route("10.4.0.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, LOCAL_AS, 65050], 250, 0, "igp"),
        Route("10.4.0.0/24", "peer_c", 65300, "192.0.2.30", "192.0.2.30", [65300, 65050], 100, 5, "igp"),
        Route("10.4.1.0/24", "peer_d", 65400, "192.0.2.40", "192.0.2.40", [65400, 65051], 100, 5, "igp"),
        Route("10.4.1.0/24", "peer_d", 65400, "192.0.2.40", "192.0.2.40", [65400, 65400], 100, 1, "igp"),
    ],
    "india": [
        Route("10.5.0.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65150], 100, 0, "igp"),
        Route("10.5.0.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65199], 150, 0, "igp"),
        Route("10.5.1.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65100, 65150], 100, 0, "igp"),
        Route("10.5.1.0/24", "peer_c", 65300, "192.0.2.30", "192.0.2.30", [65300, 65150], 100, 0, "igp"),
    ],
    "juliet": [
        Route("10.6.0.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65210], 100, 0, "igp"),
        Route("10.6.0.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65210], 120, 0, "igp"),
        Route("10.6.1.0/24", "peer_a", 65100, "192.0.2.10", "192.0.2.10", [65100, 65211], 100, 0, "igp"),
        Route("10.6.1.0/24", "peer_b", 65200, "192.0.2.20", "192.0.2.20", [65200, 65211], 150, 0, "igp"),
    ],
}

TRUST: dict[str, dict] = {
    "alpha": {
        "roa": [
            {"prefix": "10.1.0.0/24", "max_length": 2, "origin_asn": 65010, "serial": 10, "state": "valid"},
            {"prefix": "10.1.1.0/24", "max_length": 3, "origin_asn": 65010, "serial": 11, "state": "valid"},
            {"prefix": "10.1.2.0/24", "max_length": 2, "origin_asn": 65011, "serial": 12, "state": "valid"},
            {"prefix": "10.1.3.0/24", "max_length": 2, "origin_asn": 65012, "serial": 13, "state": "valid"},
        ],
        "quarantine": [{"prefix": "10.1.1.0/24", "peer": "peer_b", "reason": "export_hold"}],
    },
    "bravo": {
        "roa": [
            {"prefix": "10.2.0.0/24", "max_length": 2, "origin_asn": 65030, "serial": 100, "state": "valid"},
            {"prefix": "10.2.1.0/24", "max_length": 2, "origin_asn": 65031, "serial": 101, "state": "valid"},
        ],
        "quarantine": [],
    },
    "charlie": {
        "roa": [
            {"prefix": "10.3.0.0/24", "max_length": 2, "origin_asn": 65040, "serial": 200, "state": "valid"},
            {"prefix": "10.3.1.0/24", "max_length": 2, "origin_asn": 65041, "serial": 201, "state": "valid"},
            {"prefix": "10.3.2.0/24", "max_length": 2, "origin_asn": 65042, "serial": 202, "state": "valid"},
        ],
        "quarantine": [{"prefix": "10.3.0.0/24", "peer": "peer_a", "reason": "stale_attestation"}],
    },
    "delta": {
        "roa": [
            {"prefix": "10.4.0.0/24", "max_length": 2, "origin_asn": 65050, "serial": 300, "state": "revoked"},
            {"prefix": "10.4.0.0/24", "max_length": 2, "origin_asn": 65050, "serial": 301, "state": "valid"},
            {"prefix": "10.4.1.0/24", "max_length": 2, "origin_asn": 65051, "serial": 302, "state": "valid"},
        ],
        "quarantine": [],
    },
    "india": {
        "roa": [
            {"prefix": "10.5.0.0/22", "max_length": 2, "origin_asn": 65150, "serial": 410, "state": "valid"},
            {"prefix": "10.5.0.0/24", "max_length": 2, "origin_asn": 65150, "serial": 412, "state": "valid"},
            {"prefix": "10.5.1.0/24", "max_length": 3, "origin_asn": 65150, "serial": 411, "state": "valid"},
        ],
        "quarantine": [],
    },
    "juliet": {
        "roa": [
            {"prefix": "10.6.0.0/24", "max_length": 2, "origin_asn": 65210, "serial": 500, "state": "revoked"},
            {"prefix": "10.6.0.0/24", "max_length": 2, "origin_asn": 65210, "serial": 501, "state": "valid"},
            {"prefix": "10.6.1.0/24", "max_length": 2, "origin_asn": 65211, "serial": 502, "state": "valid"},
        ],
        "quarantine": [{"prefix": "10.6.1.0/24", "peer": "peer_b", "reason": "stale_attestation"}],
    },
}

POL = Policy(LOCAL_AS, ROUTER_ID, always_compare_med=False)


def origin_as(route: Route) -> int:
    return route.as_path[-1] if route.as_path else route.peer_as


def prefix_covered(route_prefix: str, roa_prefix: str) -> bool:
    net = ipaddress.ip_network(route_prefix, strict=False)
    roa = ipaddress.ip_network(roa_prefix, strict=False)
    return net.subnet_of(roa) or net == roa


def roa_rows_for(route: Route, roa_rows: list[dict], *, strict: bool) -> list[dict]:
    if not roa_rows:
        return []
    if not strict:
        return [row for row in roa_rows if row["prefix"] == route.prefix]
    origin = origin_as(route)
    matched: list[dict] = []
    for row in roa_rows:
        if not prefix_covered(route.prefix, row["prefix"]):
            continue
        if row["origin_asn"] != origin:
            continue
        if len(route.as_path) > row["max_length"]:
            continue
        matched.append(row)
    return matched


def roa_match(route: Route, roa_rows: list[dict], *, strict: bool) -> bool:
    if not roa_rows:
        return True
    if not strict:
        return any(row["prefix"] == route.prefix for row in roa_rows)
    matched = roa_rows_for(route, roa_rows, strict=True)
    for row in matched:
        if row["state"] == "valid":
            return True
    return False


def revoke_active(route: Route, roa_rows: list[dict], *, strict: bool) -> bool:
    if not strict:
        return True
    matched = roa_rows_for(route, roa_rows, strict=True)
    if not matched:
        return len(roa_rows) == 0
    best = max(matched, key=lambda row: row["serial"])
    return best["state"] == "valid"


def quarantine_hold(route: Route, holds: list[dict], *, strict: bool) -> bool:
    for row in holds:
        if strict:
            if row["prefix"] == route.prefix and row["peer"] == route.peer:
                return True
        elif row["peer"] == route.peer:
            return True
    return False


def guard_admit(route: Route, trust: dict, *, strict: bool) -> bool:
    if has_loop(route, POL.local_as):
        return False
    if quarantine_hold(route, trust.get("quarantine", []), strict=strict):
        return False
    roa_rows = trust.get("roa", [])
    if not roa_match(route, roa_rows, strict=strict):
        return False
    return revoke_active(route, roa_rows, strict=strict)


def pick_routes(routes: list[Route], pol: Policy) -> Route | None:
    admitted = [r for r in routes if not has_loop(r, pol.local_as)]
    if not admitted:
        return None
    best = admitted[0]
    for r in admitted[1:]:
        if compare_routes(r, best, pol) > 0:
            best = r
    return best


def ground_truth() -> tuple[dict, list[dict]]:
    fib: dict[str, list[dict]] = {}
    leaks: list[dict] = []
    for sid, routes in SCENARIOS.items():
        trust = TRUST[sid]
        by_prefix: dict[str, list[Route]] = {}
        for r in routes:
            by_prefix.setdefault(r.prefix, []).append(r)
        fib[sid] = []
        for prefix in sorted(by_prefix):
            group = by_prefix[prefix]
            strict_pool = [r for r in group if guard_admit(r, trust, strict=True)]
            loose_pool = [r for r in group if guard_admit(r, trust, strict=False)]
            correct = pick_routes(strict_pool, POL)
            stock = pick_routes(loose_pool, POL)
            assert correct is not None
            fib[sid].append(
                {
                    "prefix": correct.prefix,
                    "peer": correct.peer,
                    "next_hop": correct.next_hop,
                    "as_path": correct.as_path,
                }
            )
            if stock and (
                stock.peer != correct.peer
                or stock.as_path != correct.as_path
            ):
                leaks.append(
                    {
                        "prefix": stock.prefix,
                        "peer": stock.peer,
                        "as_path": stock.as_path,
                    }
                )
    leaks.sort(key=lambda x: (x["prefix"], x["peer"]))
    return fib, leaks


FIB_GT, LEAKS_GT = ground_truth()


def rib_json(route: Route) -> dict:
    return {
        "prefix": route.prefix,
        "next_hop": route.next_hop,
        "as_path": route.as_path,
        "local_pref": route.local_pref,
        "med": route.med,
        "origin": route.origin,
    }


def write_scenarios() -> None:
    peers = {
        "peer_a": {"as": 65100, "addr": "192.0.2.10"},
        "peer_b": {"as": 65200, "addr": "192.0.2.20"},
        "peer_c": {"as": 65300, "addr": "192.0.2.30"},
        "peer_d": {"as": 65400, "addr": "192.0.2.40"},
    }
    peer_routes: dict[str, dict[str, list[Route]]] = {sid: {} for sid in SCENARIOS}
    for sid, routes in SCENARIOS.items():
        for r in routes:
            peer_routes[sid].setdefault(r.peer, []).append(r)
    for sid, pmap in peer_routes.items():
        manifest_peers = []
        for peer in sorted(pmap):
            rib_path = f"ribs/{peer}.json"
            manifest_peers.append({"name": peer, "rib": rib_path, **peers[peer]})
            entries = [rib_json(r) for r in sorted(pmap[peer], key=lambda x: x.prefix)]
            w(
                f"environment/data/scenarios/{sid}/{rib_path}",
                json.dumps({"peer": peer, "routes": entries}, indent=2) + "\n",
            )
        w(
            f"environment/data/scenarios/{sid}/manifest.json",
            json.dumps({"id": sid, "peers": manifest_peers}, indent=2) + "\n",
        )
        trust = TRUST[sid]
        w(
            f"environment/data/scenarios/{sid}/roa.json",
            json.dumps({"entries": trust["roa"]}, indent=2) + "\n",
        )
        w(
            f"environment/data/scenarios/{sid}/quarantine.json",
            json.dumps({"holds": trust["quarantine"]}, indent=2) + "\n",
        )


def write_go_sources() -> None:
    w(
        "environment/go.mod",
        """
        module bgplab

        go 1.24

        require github.com/pelletier/go-toml/v2 v2.2.3
        """,
    )
    w(
        "environment/internal/ingest/types.go",
        """
        package ingest

        type Route struct {
            Prefix    string `json:"prefix"`
            NextHop   string `json:"next_hop"`
            ASPath    []int  `json:"as_path"`
            LocalPref int    `json:"local_pref"`
            MED       int    `json:"med"`
            Origin    string `json:"origin"`
        }

        type RibFile struct {
            Peer   string  `json:"peer"`
            Routes []Route `json:"routes"`
        }

        type PeerMeta struct {
            Name string `json:"name"`
            Rib  string `json:"rib"`
            AS   int    `json:"as"`
            Addr string `json:"addr"`
        }

        type Manifest struct {
            ID    string     `json:"id"`
            Peers []PeerMeta `json:"peers"`
        }
        """,
    )
    w(
        "environment/internal/ingest/parse.go",
        """
        package ingest

        import (
            "encoding/json"
            "os"
            "sort"
        )

        type LoadedRoute struct {
            Scenario string
            Peer     string
            PeerAS   int
            PeerAddr string
            Route
        }

        func LoadManifest(path string) (Manifest, error) {
            raw, err := os.ReadFile(path)
            if err != nil {
                return Manifest{}, err
            }
            var m Manifest
            if err := json.Unmarshal(raw, &m); err != nil {
                return Manifest{}, err
            }
            sort.Slice(m.Peers, func(i, j int) bool { return m.Peers[i].Name < m.Peers[j].Name })
            return m, nil
        }

        func LoadRib(base, rel string) (RibFile, error) {
            raw, err := os.ReadFile(base + "/" + rel)
            if err != nil {
                return RibFile{}, err
            }
            var r RibFile
            if err := json.Unmarshal(raw, &r); err != nil {
                return RibFile{}, err
            }
            sort.Slice(r.Routes, func(i, j int) bool { return r.Routes[i].Prefix < r.Routes[j].Prefix })
            return r, nil
        }

        func LoadScenario(dir string) ([]LoadedRoute, error) {
            m, err := LoadManifest(dir + "/manifest.json")
            if err != nil {
                return nil, err
            }
            var out []LoadedRoute
            for _, p := range m.Peers {
                rib, err := LoadRib(dir, p.Rib)
                if err != nil {
                    return nil, err
                }
                for _, rt := range rib.Routes {
                    out = append(out, LoadedRoute{
                        Scenario: m.ID,
                        Peer:     p.Name,
                        PeerAS:   p.AS,
                        PeerAddr: p.Addr,
                        Route:    rt,
                    })
                }
            }
            sort.Slice(out, func(i, j int) bool {
                if out[i].Prefix != out[j].Prefix {
                    return out[i].Prefix < out[j].Prefix
                }
                return out[i].Peer < out[j].Peer
            })
            return out, nil
        }
        """,
    )
    w(
        "environment/internal/policy/types.go",
        """
        package policy

        type Config struct {
            LocalAS          int    `toml:"local_as"`
            RouterID         string `toml:"router_id"`
            AlwaysCompareMED bool   `toml:"always_compare_med"`
        }
        """,
    )
    w(
        "environment/internal/policy/load.go",
        """
        package policy

        import (
            "os"

            "github.com/pelletier/go-toml/v2"
        )

        func Load(path string) (Config, error) {
            raw, err := os.ReadFile(path)
            if err != nil {
                return Config{}, err
            }
            var cfg Config
            if err := toml.Unmarshal(raw, &cfg); err != nil {
                return Config{}, err
            }
            return cfg, nil
        }
        """,
    )
    w(
        "environment/internal/kernel/check.go",
        """
        package kernel

        func containsASN(path []int, asn int) bool {
            for _, hop := range path {
                if hop == asn {
                    return true
                }
            }
            return false
        }

        func Ok_m2(path []int, local int) bool {
            return !containsASN(path, local)
        }
        """,
    )
    w(
        "environment/internal/kernel/rank.go",
        """
        package kernel

        import (
            "bgplab/internal/ingest"
            "bgplab/internal/policy"
        )

        func originRank(o string) int {
            switch o {
            case "igp":
                return 0
            case "egp":
                return 1
            case "incomplete":
                return 2
            default:
                return 3
            }
        }

        func neighborAS(r ingest.LoadedRoute) int {
            if len(r.ASPath) > 0 {
                return r.ASPath[0]
            }
            return r.PeerAS
        }

        func medComparable(a, b ingest.LoadedRoute, cfg policy.Config) bool {
            if cfg.AlwaysCompareMED {
                return true
            }
            return neighborAS(a) == neighborAS(b)
        }

        func shorterASPath(a, b []int) bool {
            if len(a) == len(b) {
                return false
            }
            return len(a) < len(b)
        }

        func Cmp_n4(a, b ingest.LoadedRoute, cfg policy.Config) bool {
            if a.LocalPref != b.LocalPref {
                return a.LocalPref > b.LocalPref
            }
            if shorterASPath(a.ASPath, b.ASPath) {
                return true
            }
            if len(a.ASPath) != len(b.ASPath) {
                return false
            }
            if originRank(a.Origin) != originRank(b.Origin) {
                return originRank(a.Origin) < originRank(b.Origin)
            }
            if medComparable(a, b, cfg) {
                if a.MED != b.MED {
                    return a.MED < b.MED
                }
            }
            return a.PeerAddr < b.PeerAddr
        }
        """,
    )
    w(
        "environment/internal/kernel/stage.go",
        """
        package kernel

        import (
            "sort"

            "bgplab/internal/ingest"
            "bgplab/internal/policy"
        )

        func Pick_r7(routes []ingest.LoadedRoute, cfg policy.Config) *ingest.LoadedRoute {
            usable := make([]ingest.LoadedRoute, 0, len(routes))
            for _, r := range routes {
                if Ok_m2(r.ASPath, cfg.LocalAS) {
                    usable = append(usable, r)
                }
            }
            sort.Slice(usable, func(i, j int) bool {
                if usable[i].Prefix != usable[j].Prefix {
                    return usable[i].Prefix < usable[j].Prefix
                }
                return usable[i].Peer < usable[j].Peer
            })
            var best *ingest.LoadedRoute
            for i := range usable {
                r := &usable[i]
                if best == nil || Cmp_n4(*r, *best, cfg) {
                    best = r
                }
            }
            return best
        }
        """,
    )
    w(
        "environment/internal/guard/types.go",
        """
        package guard

        type RoaEntry struct {
            Prefix    string `json:"prefix"`
            MaxLength int    `json:"max_length"`
            OriginASN int    `json:"origin_asn"`
            Serial    int    `json:"serial"`
            State     string `json:"state"`
        }

        type RoaDoc struct {
            Entries []RoaEntry `json:"entries"`
        }

        type HoldEntry struct {
            Prefix string `json:"prefix"`
            Peer   string `json:"peer"`
            Reason string `json:"reason"`
        }

        type QuarantineDoc struct {
            Holds []HoldEntry `json:"holds"`
        }

        type Tables struct {
            Roa         RoaDoc
            Quarantine  QuarantineDoc
        }
        """,
    )
    w(
        "environment/internal/guard/load.go",
        """
        package guard

        import (
            "encoding/json"
            "os"
            "path/filepath"
            "sort"
        )

        func LoadTables(scenarioDir string) (Tables, error) {
            var out Tables
            roaRaw, err := os.ReadFile(filepath.Join(scenarioDir, "roa.json"))
            if err != nil {
                return Tables{}, err
            }
            if err := json.Unmarshal(roaRaw, &out.Roa); err != nil {
                return Tables{}, err
            }
            qRaw, err := os.ReadFile(filepath.Join(scenarioDir, "quarantine.json"))
            if err != nil {
                return Tables{}, err
            }
            if err := json.Unmarshal(qRaw, &out.Quarantine); err != nil {
                return Tables{}, err
            }
            compactRoa(&out.Roa)
            return out, nil
        }

        func compactRoa(doc *RoaDoc) {
            if len(doc.Entries) <= 1 {
                return
            }
            sort.Slice(doc.Entries, func(i, j int) bool {
                if doc.Entries[i].Prefix != doc.Entries[j].Prefix {
                    return doc.Entries[i].Prefix < doc.Entries[j].Prefix
                }
                return doc.Entries[i].Serial < doc.Entries[j].Serial
            })
            kept := make([]RoaEntry, 0, len(doc.Entries))
            var last string
            for _, row := range doc.Entries {
                if row.Prefix == last {
                    continue
                }
                kept = append(kept, row)
                last = row.Prefix
            }
            doc.Entries = kept
        }
        """,
    )
    w(
        "environment/internal/guard/roa.go",
        """
        package guard

        import "bgplab/internal/ingest"

        func routeOrigin(path []int, peerAS int) int {
            if len(path) == 0 {
                return peerAS
            }
            return path[0]
        }

        func prefixExact(routePrefix, roaPrefix string) bool {
            return routePrefix == roaPrefix
        }

        func MatchRoa(r ingest.LoadedRoute, doc RoaDoc) bool {
            if len(doc.Entries) == 0 {
                return true
            }
            origin := routeOrigin(r.ASPath, r.PeerAS)
            for _, row := range doc.Entries {
                if !prefixExact(r.Prefix, row.Prefix) {
                    continue
                }
                if row.OriginASN != origin {
                    continue
                }
                if len(r.ASPath) >= row.MaxLength {
                    continue
                }
                if row.State != "valid" {
                    continue
                }
                return true
            }
            return false
        }
        """,
    )
    w(
        "environment/internal/guard/quarantine.go",
        """
        package guard

        import "bgplab/internal/ingest"

        func Held(r ingest.LoadedRoute, doc QuarantineDoc) bool {
            for _, row := range doc.Holds {
                if row.Prefix != r.Prefix || row.Peer != r.Peer {
                    continue
                }
                if row.Reason != "export_hold" {
                    continue
                }
                return true
            }
            return false
        }
        """,
    )
    w(
        "environment/internal/guard/revoke.go",
        """
        package guard

        import "bgplab/internal/ingest"

        func RevokeActive(r ingest.LoadedRoute, doc RoaDoc) bool {
            if len(doc.Entries) == 0 {
                return true
            }
            origin := routeOrigin(r.ASPath, r.PeerAS)
            var picked *RoaEntry
            for _, row := range doc.Entries {
                if !prefixExact(r.Prefix, row.Prefix) {
                    continue
                }
                if row.OriginASN != origin {
                    continue
                }
                if len(r.ASPath) >= row.MaxLength {
                    continue
                }
                copy := row
                if picked == nil || copy.Serial < picked.Serial {
                    picked = &copy
                }
            }
            return picked != nil && picked.State == "valid"
        }
        """,
    )
    w(
        "environment/internal/guard/gate.go",
        """
        package guard

        import (
            "bgplab/internal/ingest"
            "bgplab/internal/kernel"
            "bgplab/internal/policy"
        )

        func Admit(r ingest.LoadedRoute, cfg policy.Config, tab Tables) bool {
            if !kernel.Ok_m2(r.ASPath, cfg.LocalAS) {
                return false
            }
            if Held(r, tab.Quarantine) {
                return false
            }
            if !MatchRoa(r, tab.Roa) {
                return false
            }
            return RevokeActive(r, tab.Roa)
        }
        """,
    )
    w(
        "environment/internal/ledger/scan.go",
        """
        package ledger

        import "hash/fnv"

        func Digest(parts ...string) uint64 {
            h := fnv.New64a()
            for _, p := range parts {
                _, _ = h.Write([]byte(p))
                _, _ = h.Write([]byte{0})
            }
            return h.Sum64()
        }
        """,
    )
    w(
        "environment/internal/mesh/topo.go",
        """
        package mesh

        import (
            "os"
            "sort"
            "strings"
        )

        func ListBundles(root string) ([]string, error) {
            entries, err := os.ReadDir(root)
            if err != nil {
                return nil, err
            }
            var out []string
            for _, e := range entries {
                if e.IsDir() {
                    out = append(out, e.Name())
                }
            }
            sort.Strings(out)
            return out, nil
        }

        func NormalizeID(id string) string {
            return strings.TrimSpace(strings.ToLower(id))
        }
        """,
    )
    w(
        "environment/internal/mesh/wire.go",
        """
        package mesh

        import "fmt"

        func Tag(id string, peer string) string {
            return fmt.Sprintf("%s:%s", id, peer)
        }
        """,
    )
    w(
        "environment/internal/util/sort.go",
        """
        package util

        import "sort"

        func StableStrings(in []string) []string {
            out := append([]string(nil), in...)
            sort.Strings(out)
            return out
        }
        """,
    )
    w(
        "environment/internal/report/emit.go",
        """
        package report

        import (
            "encoding/json"
            "os"
            "sort"

            "bgplab/internal/guard"
            "bgplab/internal/ingest"
            "bgplab/internal/kernel"
            "bgplab/internal/policy"
        )

        type FibEntry struct {
            Prefix   string `json:"prefix"`
            Peer     string `json:"peer"`
            NextHop  string `json:"next_hop"`
            ASPath   []int  `json:"as_path"`
        }

        type LeakItem struct {
            Prefix  string `json:"prefix"`
            Peer    string `json:"peer"`
            ASPath  []int  `json:"as_path"`
        }

        type FibDoc map[string][]FibEntry
        type LeakDoc struct {
            Items []LeakItem `json:"items"`
        }

        func stockHeld(r ingest.LoadedRoute, doc guard.QuarantineDoc) bool {
            for _, row := range doc.Holds {
                if row.Peer == r.Peer {
                    return true
                }
            }
            return false
        }

        func stockRoa(r ingest.LoadedRoute, doc guard.RoaDoc) bool {
            for _, row := range doc.Entries {
                if row.Prefix == r.Prefix {
                    return true
                }
            }
            return len(doc.Entries) == 0
        }

        func stockAdmit(r ingest.LoadedRoute, cfg policy.Config, tab guard.Tables) bool {
            if !kernel.Ok_m2(r.ASPath, cfg.LocalAS) {
                return false
            }
            if stockHeld(r, tab.Quarantine) {
                return false
            }
            return stockRoa(r, tab.Roa)
        }

        func filterAdmit(routes []ingest.LoadedRoute, cfg policy.Config, tab guard.Tables, admit func(ingest.LoadedRoute, policy.Config, guard.Tables) bool) []ingest.LoadedRoute {
            out := make([]ingest.LoadedRoute, 0, len(routes))
            for _, r := range routes {
                if admit(r, cfg, tab) {
                    out = append(out, r)
                }
            }
            return out
        }

        func routesDiffer(a, b *ingest.LoadedRoute) bool {
            if a == nil || b == nil {
                return a != b
            }
            if a.Peer != b.Peer {
                return true
            }
            if len(a.ASPath) != len(b.ASPath) {
                return true
            }
            for i := range a.ASPath {
                if a.ASPath[i] != b.ASPath[i] {
                    return true
                }
            }
            return false
        }

        func Build(routes []ingest.LoadedRoute, cfg policy.Config, tables map[string]guard.Tables) (FibDoc, LeakDoc) {
            byScenario := map[string]map[string][]ingest.LoadedRoute{}
            for _, r := range routes {
                if _, ok := byScenario[r.Scenario]; !ok {
                    byScenario[r.Scenario] = map[string][]ingest.LoadedRoute{}
                }
                byScenario[r.Scenario][r.Prefix] = append(byScenario[r.Scenario][r.Prefix], r)
            }
            fib := FibDoc{}
            var leaks []LeakItem
            scenarios := make([]string, 0, len(byScenario))
            for s := range byScenario {
                scenarios = append(scenarios, s)
            }
            sort.Strings(scenarios)
            for _, sid := range scenarios {
                tab := tables[sid]
                prefixes := make([]string, 0, len(byScenario[sid]))
                for p := range byScenario[sid] {
                    prefixes = append(prefixes, p)
                }
                sort.Strings(prefixes)
                for _, p := range prefixes {
                    group := byScenario[sid][p]
                    corrected := filterAdmit(group, cfg, tab, guard.Admit)
                    baseline := filterAdmit(group, cfg, tab, stockAdmit)
                    chosen := kernel.Pick_r7(corrected, cfg)
                    shadow := kernel.Pick_r7(baseline, cfg)
                    if chosen != nil {
                        fib[sid] = append(fib[sid], FibEntry{
                            Prefix:  chosen.Prefix,
                            Peer:    chosen.Peer,
                            NextHop: chosen.NextHop,
                            ASPath:  chosen.ASPath,
                        })
                    }
                    if routesDiffer(shadow, chosen) && shadow != nil {
                        leaks = append(leaks, LeakItem{Prefix: shadow.Prefix, Peer: shadow.Peer, ASPath: shadow.ASPath})
                    }
                }
            }
            sort.Slice(leaks, func(i, j int) bool {
                if leaks[i].Prefix != leaks[j].Prefix {
                    return leaks[i].Prefix < leaks[j].Prefix
                }
                return leaks[i].Peer < leaks[j].Peer
            })
            return fib, LeakDoc{Items: leaks}
        }

        func WriteJSON(path string, v any) error {
            raw, err := json.MarshalIndent(v, "", "  ")
            if err != nil {
                return err
            }
            raw = append(raw, '\\n')
            return os.WriteFile(path, raw, 0o644)
        }
        """,
    )
    w(
        "environment/cmd/converge/main.go",
        """
        package main

        import (
            "flag"
            "fmt"
            "log"
            "os"
            "path/filepath"

            "bgplab/internal/guard"
            "bgplab/internal/ingest"
            "bgplab/internal/mesh"
            "bgplab/internal/policy"
            "bgplab/internal/report"
        )

        func main() {
            polPath := flag.String("policy", "{TASK_ROOT}/data/policy.toml", "policy file")
            scenRoot := flag.String("scenarios", "{TASK_ROOT}/data/scenarios", "scenario root")
            outDir := flag.String("out", "{OUTPUT_ROOT}", "output directory")
            flag.Parse()

            cfg, err := policy.Load(*polPath)
            if err != nil {
                log.Fatal(err)
            }
            bundles, err := mesh.ListBundles(*scenRoot)
            if err != nil {
                log.Fatal(err)
            }
            var all []ingest.LoadedRoute
            tables := map[string]guard.Tables{}
            for _, b := range bundles {
                dir := filepath.Join(*scenRoot, b)
                tab, err := guard.LoadTables(dir)
                if err != nil {
                    log.Fatal(err)
                }
                tables[b] = tab
                loaded, err := ingest.LoadScenario(dir)
                if err != nil {
                    log.Fatal(err)
                }
                all = append(all, loaded...)
            }
            fib, leaks := report.Build(all, cfg, tables)
            if err := os.MkdirAll(*outDir, 0o755); err != nil {
                log.Fatal(err)
            }
            if err := report.WriteJSON(filepath.Join(*outDir, "fib.json"), fib); err != nil {
                log.Fatal(err)
            }
            if err := report.WriteJSON(filepath.Join(*outDir, "leaks.json"), leaks); err != nil {
                log.Fatal(err)
            }
            fmt.Println("converged")
        }
        """,
    )
    w(
        "environment/cmd/audit/main.go",
        """
        package main

        import (
            "flag"
            "fmt"
            "log"

            "bgplab/internal/ledger"
            "bgplab/internal/mesh"
        )

        func main() {
            root := flag.String("root", "{TASK_ROOT}/data/scenarios", "scenario root")
            flag.Parse()
            ids, err := mesh.ListBundles(*root)
            if err != nil {
                log.Fatal(err)
            }
            var sum uint64
            for _, id := range ids {
                sum ^= ledger.Digest(id)
            }
            fmt.Printf("audit:%x\\n", sum)
        }
        """,
    )


def write_docs_and_config() -> None:
    w(
        "environment/data/policy.toml",
        f"""
        local_as = {LOCAL_AS}
        router_id = "{ROUTER_ID}"
        always_compare_med = false
        """,
    )
    w(
        "environment/docs/scenario-notes.md",
        """
        Six scenario bundles arrived after an overnight RPKI attestation refresh. Each directory under data/scenarios carries adjacency exports, roa.json origin attestations, and quarantine.json export-policy holds.

        alpha — Edge aggregation lab. Four prefixes share two upstream peers. One export hold targets a longer AS-path alternative for a single prefix. A neighboring prefix shows a higher local preference from an alternate peer whose origin does not match bundled attestations.

        bravo — Metro handoff desk. Two prefixes compete across peers where MED and path length interact. One prefix advertises two paths through the same peer, including an AS-loop shaped export that should never win.

        charlie — Research WAN. Three campus prefixes share two peers. One peer carries a stale-attestation hold on a single prefix while another prefix still accepts exports from that peer.

        delta — Peering refresh window. One prefix received a superseded revoked attestation followed by a higher-serial valid row. Another prefix advertises two paths through the same peer where only the non-looping path should remain.

        india — IX rollup desk. Aggregate attestations cover more-specific prefixes. One export shows an origin mismatch that should lose to an attested path. Another prefix tests whether rollup coverage and path-length limits are evaluated together.

        juliet — Transit re-home. Attestation rows for one prefix include both revoked and valid serials. A second prefix carries a non-export hold reason on one peer while the other peer still offers a valid path.

        Observed trust failures: several bundles install routes whose origins, holds, or attestation serials disagree with bundled trust material. The route-leak security ledger is empty.
        """,
    )
    w(
        "environment/docs/format-notes.md",
        """
        Adjacency exports are JSON objects with a peer name and a routes array.
        Each route row carries prefix, next_hop, as_path, local_pref, med, and origin.
        Scenario manifests list peers and relative rib paths.
        Each bundle also ships roa.json with RPKI attestation rows and quarantine.json with export-policy holds.

        quarantine.json holds are scoped by prefix and peer. Corrected trust admission must treat any
        matching hold row as blocking, regardless of the reason value on that row.

        fib.json maps each bundle id to an ordered list of chosen routes (prefix, peer, next_hop, as_path).
        Only routes that survive attestation, revocation freshness, and quarantine policy may appear.

        leaks.json is the route-leak security ledger. It carries an items array. Converge fills items from a per-prefix comparison between the frozen stock admission baseline wired into the report layer and corrected trust admission that drives fib.json. When those winners differ on peer or as_path, append the stock winner with those three fields. Omit prefixes where both passes agree or where stock admission rejects every candidate. Sort items by prefix then peer ascending.

        Converge accepts --policy, --scenarios, and --out. A typical invocation is:
        /opt/bgplab/bin/converge --policy /opt/bgplab/data/policy.toml --scenarios /opt/bgplab/data/scenarios --out /output
        """,
    )
    w(
        "environment/requirements.txt",
        """
        exceptiongroup==1.3.1 \\
            --hash=sha256:a7a39a3bd276781e98394987d3a5701d0c4edffb633bb7a5144577f82c773598
        iniconfig==2.3.0 \\
            --hash=sha256:f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12
        packaging==26.2 \\
            --hash=sha256:5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e
        pluggy==1.6.0 \\
            --hash=sha256:e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
        pygments==2.20.0 \\
            --hash=sha256:81a9e26dd42fd28a23a2d169d86d7ac03b46e2f8b59ed4698fb4785f946d0176
        pytest==8.4.1 \\
            --hash=sha256:539c70ba6fcead8e78eebbf1115e8b589e7565830d7d006a8723f19ac8a0afb7
        pytest-json-ctrf==0.3.5 \\
            --hash=sha256:e82fd1d69be2f92385bc33540063e5ad7b17b36de67764c84f3ceb9815a895e9
        tomli==2.4.1 \\
            --hash=sha256:0d85819802132122da43cb86656f8d1f8c6587d54ae7dcaf30e90533028b49fe
        typing-extensions==4.16.0 \\
            --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8
        """,
    )
    w(
        "environment/.dockerignore",
        """
        .git
        .gitignore
        **/__pycache__/
        **/*.pyc
        **/.pytest_cache/
        **/.mypy_cache/
        **/.ruff_cache/
        **/node_modules/
        **/target/
        **/dist/
        **/build/
        **/.venv/
        **/venv/
        .env
        *.log
        solution/
        tests/
        """,
    )
    w(
        "environment/Dockerfile",
        f"""
        # syntax=docker/dockerfile:1

        FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

        WORKDIR /build
        COPY go.mod go.sum ./
        RUN go mod download
        COPY cmd/ ./cmd/
        COPY internal/ ./internal/
        RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/converge ./cmd/converge \\
            && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/audit ./cmd/audit

        FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

        LABEL org.opencontainers.image.source="terminal-bench-3"
        LABEL org.opencontainers.image.version="1.0.0"
        LABEL org.opencontainers.image.licenses="MIT"

        # Agent runtime requires tmux and asciinema before any other setup.
        RUN apt-get update \\
            && apt-get install -y --no-install-recommends \\
                asciinema=2.2.0-1 \\
                tmux=3.3a-3 \\
                bash \\
                ca-certificates \\
                procps \\
                python3 \\
                python3-pip \\
            && rm -rf /var/lib/apt/lists/*

        ENV TERM=xterm-256color

        RUN tmux -V && asciinema --version

        COPY requirements.txt /tmp/requirements.txt
        # Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
        RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \\
            -r /tmp/requirements.txt
        RUN rm -f /tmp/requirements.txt

        ENV GOPATH=/go \\
            GOCACHE=/tmp/go-cache
        RUN mkdir -p /go /tmp/go-cache

        COPY go.mod go.sum {TASK_ROOT}/
        RUN cd {TASK_ROOT} && go mod download

        COPY --from=builder --chmod=755 /out/converge {TASK_ROOT}/bin/converge
        COPY --from=builder --chmod=755 /out/audit {TASK_ROOT}/bin/audit
        COPY cmd/ {TASK_ROOT}/cmd/
        COPY internal/ {TASK_ROOT}/internal/
        COPY data/ {TASK_ROOT}/data/
        COPY docs/ {TASK_ROOT}/docs/

        RUN tmux -V \\
            && asciinema --version \\
            && tmux new-session -d -s _smoke \\
            && tmux has-session -t _smoke \\
            && tmux kill-session -t _smoke

        WORKDIR {TASK_ROOT}
        ENV PATH="{TASK_ROOT}/bin:${{PATH}}"
        """,
    )


def write_task_meta() -> None:
    w(
        "instruction.md",
        """
        After a regional RPKI attestation cutover, six scenario bundles under `{TASK_ROOT}/data/scenarios` carry adjacency exports, origin attestations, and export-policy quarantine feeds. Bundle context and observed trust failures are documented in `{TASK_ROOT}/docs/scenario-notes.md`. Trust-admission sources live under `{TASK_ROOT}`.

        `{TASK_ROOT}/bin/converge` must apply `{TASK_ROOT}/data/policy.toml` and produce `{OUTPUT_ROOT}/fib.json` plus `{OUTPUT_ROOT}/leaks.json`. Published FIB entries must be consistent with bundled ROA attestation, revocation freshness, and quarantine policy. The route-leak security ledger must record stock-versus-corrected admission divergences. The current snapshot finishes cleanly yet installs routes that disagree with trust material, and the leak ledger is empty.

        `{OUTPUT_ROOT}/fib.json` maps each bundle id to chosen route rows naming prefix, peer, next_hop, and as_path. `{OUTPUT_ROOT}/leaks.json` wraps an items array whose rows name prefix, peer, and as_path. Quarantine hold matching, output layout, CLI flags, and leak-ledger semantics are documented in `{TASK_ROOT}/docs/format-notes.md`. Outputs must be deterministic and must not depend on filesystem iteration order or wall clock.
        """,
    )
    w(
        "task.toml",
        """
        version = "2.0"

        [metadata]
        author_name = "anonymous"
        author_email = "anonymous"
        difficulty = "hard"
        category = "security"
        subcategories = []
        number_of_milestones = 0
        codebase_size = "small"
        languages = ["go", "bash"]
        tags = ["security", "rpki", "roa", "attestation", "quarantine", "go"]
        expert_time_estimate_min = 120
        junior_time_estimate_min = 300

        [verifier]
        timeout_sec = 600

        [agent]
        timeout_sec = 1200

        [environment]
        allow_internet = false
        build_timeout_sec = 600
        cpus = 2
        memory_mb = 4096
        storage_mb = 10240
        """,
    )
    w(
        "output_contract.toml",
        """
        user_visible_outputs = [
          "{OUTPUT_ROOT}/fib.json",
          "{OUTPUT_ROOT}/leaks.json",
        ]

        internal_harness_files = []

        [structured_outputs.fib]
        target = "{OUTPUT_ROOT}/fib.json"
        format = "json"
        instruction_checks = ["prefix", "peer", "next_hop", "as_path"]

        [structured_outputs.leaks]
        target = "{OUTPUT_ROOT}/leaks.json"
        format = "json"
        instruction_checks = ["items", "prefix", "peer", "as_path"]
        """,
    )
    w(
        "tests/test.sh",
        """
        #!/bin/bash

        # Verifier dependencies are installed in environment/Dockerfile.
        # Add task-specific verifier-only Python packages there, not here.

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


def write_tests() -> None:
    fib_json = json.dumps(FIB_GT, indent=2)
    leaks_json = json.dumps({"items": LEAKS_GT}, indent=2)
    body = f'''import json
import shutil
import subprocess

import pytest
from pathlib import Path

OPT = Path("{TASK_ROOT}")
OUT = Path("{OUTPUT_ROOT}")
CONVERGE = OPT / "bin" / "converge"

FIB_GT = json.loads("""{fib_json}""")
LEAKS_GT = json.loads("""{leaks_json}""")


def run_tool():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    subprocess.run(
        ["go", "build", "-o", "bin/converge", "./cmd/converge"],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    subprocess.run(
        [
            str(CONVERGE),
            "--policy",
            "{TASK_ROOT}/data/policy.toml",
            "--scenarios",
            "{TASK_ROOT}/data/scenarios",
            "--out",
            "{OUTPUT_ROOT}",
        ],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    fib = json.loads((OUT / "fib.json").read_text())
    leaks = json.loads((OUT / "leaks.json").read_text())
    return fib, leaks


@pytest.fixture(scope="module")
def tool_output():
    return run_tool()


def test_golf(tool_output):
    """Declared output artifacts exist at the instructed paths."""
    assert (OUT / "fib.json").is_file()
    assert (OUT / "leaks.json").is_file()


def test_hotel(tool_output):
    """Back-to-back runs emit identical fib and leak payloads."""
    first_fib, first_leaks = tool_output
    second_fib, second_leaks = run_tool()
    assert second_fib == first_fib
    assert second_leaks == first_leaks


def test_alpha(tool_output):
    """Alpha edge lab: attested origins win and export holds block only their scoped prefix."""
    fib, _ = tool_output
    assert fib["alpha"] == FIB_GT["alpha"]


def test_bravo(tool_output):
    """Bravo metro desk: loop-shaped exports lose and MED-aware selection respects neighbors."""
    fib, _ = tool_output
    assert fib["bravo"] == FIB_GT["bravo"]


def test_charlie(tool_output):
    """Charlie research WAN: stale-attestation holds apply per prefix without starving siblings."""
    fib, _ = tool_output
    assert fib["charlie"] == FIB_GT["charlie"]


def test_delta(tool_output):
    """Delta peering refresh: newest attestation serial governs after a revoked row is superseded."""
    fib, _ = tool_output
    assert fib["delta"] == FIB_GT["delta"]


def test_india(tool_output):
    """India IX rollup: aggregate attestations cover specifics and path-length limits bind correctly."""
    fib, _ = tool_output
    assert fib["india"] == FIB_GT["india"]


def test_juliet(tool_output):
    """Juliet transit re-home: non-export holds block peers and serial rivalry picks the valid row."""
    fib, _ = tool_output
    assert fib["juliet"] == FIB_GT["juliet"]


def test_echo(tool_output):
    """Leak ledger is populated, sorted, and uses the instructed item shape."""
    _, leaks = tool_output
    items = leaks.get("items")
    assert isinstance(items, list)
    assert items, "expected a non-empty leak catalog after trust repair"
    assert items == sorted(items, key=lambda x: (x["prefix"], x["peer"]))
    for row in items:
        assert isinstance(row.get("prefix"), str)
        assert isinstance(row.get("peer"), str)
        assert isinstance(row.get("as_path"), list)
        assert row["as_path"]


def test_foxtrot(tool_output):
    """All bundles present and leak ledger matches the stock-versus-corrected divergences."""
    fib, leaks = tool_output
    assert set(fib) == {{"alpha", "bravo", "charlie", "delta", "india", "juliet"}}
    assert leaks == LEAKS_GT
'''
    (TASK / "tests" / "test_outputs.py").write_text(body, encoding="utf-8")


def write_solve() -> None:
    w(
        "solution/solve.sh",
        """
        #!/bin/bash
        set -euo pipefail
        cd {TASK_ROOT}
        cat > internal/guard/load.go <<'GO'
        package guard

        import (
            "encoding/json"
            "os"
            "path/filepath"
            "sort"
        )

        func LoadTables(scenarioDir string) (Tables, error) {
            var out Tables
            roaRaw, err := os.ReadFile(filepath.Join(scenarioDir, "roa.json"))
            if err != nil {
                return Tables{}, err
            }
            if err := json.Unmarshal(roaRaw, &out.Roa); err != nil {
                return Tables{}, err
            }
            qRaw, err := os.ReadFile(filepath.Join(scenarioDir, "quarantine.json"))
            if err != nil {
                return Tables{}, err
            }
            if err := json.Unmarshal(qRaw, &out.Quarantine); err != nil {
                return Tables{}, err
            }
            orderRoaRows(&out.Roa)
            return out, nil
        }

        func orderRoaRows(doc *RoaDoc) {
            if len(doc.Entries) <= 1 {
                return
            }
            sort.Slice(doc.Entries, func(i, j int) bool {
                if doc.Entries[i].Prefix != doc.Entries[j].Prefix {
                    return doc.Entries[i].Prefix < doc.Entries[j].Prefix
                }
                if doc.Entries[i].Serial != doc.Entries[j].Serial {
                    return doc.Entries[i].Serial < doc.Entries[j].Serial
                }
                return doc.Entries[i].OriginASN < doc.Entries[j].OriginASN
            })
        }
        GO
        cat > internal/guard/roa.go <<'GO'
        package guard

        import (
            "net"

            "bgplab/internal/ingest"
        )

        func originASN(path []int, peerAS int) int {
            if len(path) == 0 {
                return peerAS
            }
            return path[len(path)-1]
        }

        func prefixCovered(routePrefix, roaPrefix string) bool {
            if routePrefix == roaPrefix {
                return true
            }
            _, routeNet, err := net.ParseCIDR(routePrefix)
            if err != nil {
                return false
            }
            _, roaNet, err := net.ParseCIDR(roaPrefix)
            if err != nil {
                return false
            }
            roaOnes, _ := roaNet.Mask.Size()
            routeOnes, _ := routeNet.Mask.Size()
            if routeOnes < roaOnes {
                return false
            }
            mask := net.CIDRMask(roaOnes, 32)
            return routeNet.IP.Mask(mask).Equal(roaNet.IP.Mask(mask))
        }

        func MatchRoa(r ingest.LoadedRoute, doc RoaDoc) bool {
            if len(doc.Entries) == 0 {
                return true
            }
            origin := originASN(r.ASPath, r.PeerAS)
            var best *RoaEntry
            for _, row := range doc.Entries {
                if !prefixCovered(r.Prefix, row.Prefix) {
                    continue
                }
                if row.OriginASN != origin {
                    continue
                }
                if len(r.ASPath) > row.MaxLength {
                    continue
                }
                if row.State != "valid" {
                    continue
                }
                copy := row
                if best == nil || copy.Serial > best.Serial {
                    best = &copy
                }
            }
            return best != nil
        }
        GO
        cat > internal/guard/quarantine.go <<'GO'
        package guard

        import "bgplab/internal/ingest"

        func Held(r ingest.LoadedRoute, doc QuarantineDoc) bool {
            for _, row := range doc.Holds {
                if row.Prefix == r.Prefix && row.Peer == r.Peer {
                    return true
                }
            }
            return false
        }
        GO
        cat > internal/guard/revoke.go <<'GO'
        package guard

        import "bgplab/internal/ingest"

        func RevokeActive(r ingest.LoadedRoute, doc RoaDoc) bool {
            origin := originASN(r.ASPath, r.PeerAS)
            var newest *RoaEntry
            for _, row := range doc.Entries {
                if !prefixCovered(r.Prefix, row.Prefix) {
                    continue
                }
                if row.OriginASN != origin {
                    continue
                }
                if len(r.ASPath) > row.MaxLength {
                    continue
                }
                copy := row
                if newest == nil || copy.Serial > newest.Serial {
                    newest = &copy
                }
            }
            return newest != nil && newest.State == "valid"
        }
        GO
        go build -o bin/converge ./cmd/converge
        bin/converge --policy {TASK_ROOT}/data/policy.toml --scenarios {TASK_ROOT}/data/scenarios --out {OUTPUT_ROOT}
        """,
    )



def write_go_sum() -> None:
    import subprocess

    go_mod = ENV / "go.mod"
    if not go_mod.exists():
        return
    # go.sum is required for reproducible builder-stage downloads; generate via canonical image.
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ENV.resolve()}:/src",
            "-w",
            "/src",
            "public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac",
            "go",
            "mod",
            "tidy",
        ],
        check=True,
    )


def main() -> None:
    import shutil

    if TASK.exists():
        shutil.rmtree(TASK)
    write_scenarios()
    write_go_sources()
    write_go_sum()
    write_docs_and_config()
    stale_operator = ENV / "docs" / "operator-notes.md"
    if stale_operator.exists():
        stale_operator.unlink()
    write_task_meta()
    write_tests()
    write_solve()
    print(f"Wrote {TASK}")
    print("FIB scenarios:", list(FIB_GT))
    print("Leaks:", LEAKS_GT)


if __name__ == "__main__":
    main()
