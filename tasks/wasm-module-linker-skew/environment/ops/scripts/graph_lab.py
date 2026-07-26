#!/usr/bin/env python3
"""Reference graph digests for a manifest epoch (verifier oracle)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

DATA = Path("/app/data")
MODULES = DATA / "modules"


def module_body(module_id: str, version: int) -> dict:
    raw = (MODULES / f"{module_id}.slot{version}.json").read_text()
    return json.loads(raw)


def module_digest(module_id: str, version: int) -> str:
    body = module_body(module_id, version)
    canon = json.dumps(body, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


def visible(epoch: int) -> list[str]:
    out: list[str] = []
    for mid, since in (("codec", 1), ("host", 1), ("filter", 3)):
        if since <= epoch:
            out.append(mid)
    return sorted(out)


def resolve_imports(epoch: int, dep_versions: dict[str, int]) -> list[dict]:
    host = module_body("host", epoch)
    rows: list[dict] = []
    for imp in host.get("imports", []):
        dep = imp["module"]
        if dep not in dep_versions:
            continue
        rows.append(
            {
                "import": f"{dep}.{imp['field']}",
                "slot": dep_versions[dep],
                "bound": imp["bind"],
            }
        )
    return sorted(rows, key=lambda r: r["import"])


def graph_at(epoch: int) -> dict:
    mods = visible(epoch)
    dep_versions = {mid: epoch for mid in mods}
    modules_out = {
        mid: {"version": epoch, "digest": module_digest(mid, epoch)} for mid in mods
    }
    imports = resolve_imports(epoch, dep_versions) if "host" in mods else []
    canon = {"epoch": epoch, "modules": modules_out, "imports": imports}
    digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "epoch": epoch,
        "graph_digest": digest,
        "modules": modules_out,
        "imports": imports,
    }


def main() -> None:
    epoch = int(sys.argv[1])
    print(json.dumps(graph_at(epoch), separators=(",", ":")))


if __name__ == "__main__":
    main()
