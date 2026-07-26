"""Verifier for the Carcassonne tile-meeple booklet.

Rebuilds every verdict from the round sheets with its own house rules and
replays each filed sequence past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

COLS = "abc"
ROWS = "123"
CELLS = [f"{c}{r}" for r in ROWS for c in COLS]
IDX = {name: i for i, name in enumerate(CELLS)}
N = len(CELLS)
# NESW
DIRS = "NESW"
DELTA = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
OPP = {"N": "S", "E": "W", "S": "N", "W": "E"}
RED, BLUE = "R", "B"
FLOOR_DEFAULT = 4
BUDGET_DEFAULT = 3


def cell_xy(name: str) -> tuple[int, int]:
    return COLS.index(name[0]), ROWS.index(name[1])


def xy_cell(x: int, y: int) -> str | None:
    if 0 <= x < 3 and 0 <= y < 3:
        return f"{COLS[x]}{ROWS[y]}"
    return None


def neighbor(cell: str, d: str) -> str | None:
    x, y = cell_xy(cell)
    dx, dy = DELTA[d]
    return xy_cell(x + dx, y + dy)


def rotate_edges(edges: str, rot: int) -> str:
    """Rotate NESW string clockwise by rot degrees (0/90/180/270)."""
    k = (rot // 90) % 4
    chars = list(edges[:4])
    for _ in range(k):
        # N->E->S->W->N
        chars = [chars[3], chars[0], chars[1], chars[2]]
    return "".join(chars)


def parse_tile_code(code: str) -> tuple[str, bool, bool]:
    """Return (edges4, cloister, pennant).

    Markers: trailing/embedded `*` = pennant, `#` or `:m` = cloister.
    """
    cloister = "#" in code or ":m" in code
    pennant = "*" in code
    core = (
        code.replace(":m", "")
        .replace("#", "")
        .replace("*", "")
        .replace("m", "")
    )
    if len(core) != 4 or any(ch not in "CRF" for ch in core):
        raise ValueError(f"bad tile code {code}")
    return core, cloister, pennant


@dataclass(frozen=True)
class Meeple:
    colour: str
    kind: str  # city|road|cloister|farm
    edge: str  # N|E|S|W|C


@dataclass(frozen=True)
class Tile:
    edges: str  # NESW after rotation
    cloister: bool = False
    pennant: bool = False


@dataclass(frozen=True)
class State:
    tiles: tuple[Tile | None, ...]
    meeples: tuple[tuple[str, Meeple], ...]  # (cell, meeple)
    hand: tuple[str, ...]
    blue_stock: int
    floor: int = FLOOR_DEFAULT
    budget: int = BUDGET_DEFAULT
    score: int = 0
    completed_cities: tuple[frozenset[str], ...] = ()

    def tile_at(self, cell: str) -> Tile | None:
        return self.tiles[IDX[cell]]

    def with_tile(self, cell: str, tile: Tile) -> State:
        arr = list(self.tiles)
        arr[IDX[cell]] = tile
        return replace(self, tiles=tuple(arr))

    def add_meeple(self, cell: str, m: Meeple) -> State:
        return replace(self, meeples=self.meeples + ((cell, m),))


def empty_tiles() -> tuple[Tile | None, ...]:
    return tuple(None for _ in range(N))


def parse_sheet(text: str) -> State:
    hand: list[str] = []
    blue_stock = 1
    floor = FLOOR_DEFAULT
    budget = BUDGET_DEFAULT
    tiles = list(empty_tiles())
    meeples: list[tuple[str, Meeple]] = []
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("board_id:"):
            continue
        if line.startswith("to_move:"):
            continue
        if line.startswith("floor:"):
            floor = int(line.split(":", 1)[1].strip())
            continue
        if line.startswith("budget:"):
            budget = int(line.split(":", 1)[1].strip())
            continue
        if line.startswith("blue_stock:"):
            blue_stock = int(line.split(":", 1)[1].strip())
            continue
        if line.startswith("hand:"):
            body = line.split(":", 1)[1].strip()
            hand = [p.strip() for p in body.split(",") if p.strip()]
            continue
        if line == "tiles:":
            section = "tiles"
            continue
        if line == "meeples:":
            section = "meeples"
            continue
        if section == "tiles":
            # b2:CRFR:0 or b2:CCCC+:0 or b2:FFFF:m:0
            parts = line.split(":")
            cell = parts[0]
            if cell not in IDX:
                raise ValueError(line)
            if len(parts) == 3:
                code, rot_s = parts[1], parts[2]
            elif len(parts) == 4 and parts[2] == "m":
                code, rot_s = parts[1] + ":m", parts[3]
            else:
                raise ValueError(line)
            edges, cloister, pennant = parse_tile_code(code)
            rot = int(rot_s)
            tiles[IDX[cell]] = Tile(rotate_edges(edges, rot), cloister, pennant)
            continue
        if section == "meeples":
            # b2:R:city:N
            cell, colour, kind, edge = line.split(":")
            meeples.append((cell, Meeple(colour, kind, edge)))
            continue
    return State(
        tiles=tuple(tiles),
        meeples=tuple(meeples),
        hand=tuple(hand),
        blue_stock=blue_stock,
        floor=floor,
        budget=budget,
    )


def edge_of(tile: Tile, d: str) -> str:
    return tile.edges[DIRS.index(d)]


def placement_legal(state: State, cell: str, tile: Tile) -> bool:
    if cell not in IDX or state.tile_at(cell) is not None:
        return False
    touched = False
    for d in DIRS:
        nb = neighbor(cell, d)
        if nb is None:
            continue
        other = state.tile_at(nb)
        if other is None:
            continue
        touched = True
        if edge_of(tile, d) != edge_of(other, OPP[d]):
            return False
    # Must touch an existing tile when the board is non-empty.
    return touched or all(t is None for t in state.tiles)


def city_components(state: State) -> list[set[tuple[str, str]]]:
    """Connected (cell, edge) nodes with C edges, linked across matching borders."""
    nodes: list[tuple[str, str]] = []
    for cell in CELLS:
        tile = state.tile_at(cell)
        if tile is None:
            continue
        for d in DIRS:
            if edge_of(tile, d) == "C":
                nodes.append((cell, d))
    parent = {n: n for n in nodes}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # On the same tile, adjacent C edges that are "same city segment" — house:
    # all C edges on one tile form one city blob if they are contiguous around
    # the tile without an F/R separator. Simpler house: all C edges on a tile
    # belong to ONE city on that tile (classic for solid city tiles).
    by_cell: dict[str, list[str]] = {}
    for cell, d in nodes:
        by_cell.setdefault(cell, []).append(d)
    for cell, edges in by_cell.items():
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                union((cell, edges[i]), (cell, edges[j]))

    for cell, d in nodes:
        nb = neighbor(cell, d)
        if nb is None:
            continue
        other = state.tile_at(nb)
        if other is None:
            continue
        if edge_of(other, OPP[d]) == "C":
            union((cell, d), (nb, OPP[d]))

    groups: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for n in nodes:
        groups.setdefault(find(n), set()).add(n)
    return list(groups.values())


def road_components(state: State) -> list[set[tuple[str, str]]]:
    nodes: list[tuple[str, str]] = []
    for cell in CELLS:
        tile = state.tile_at(cell)
        if tile is None:
            continue
        for d in DIRS:
            if edge_of(tile, d) == "R":
                nodes.append((cell, d))
    parent = {n: n for n in nodes}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_cell: dict[str, list[str]] = {}
    for cell, d in nodes:
        by_cell.setdefault(cell, []).append(d)
    for cell, edges in by_cell.items():
        # Road edges on a tile join if opposite (straight) or all if junction —
        # house: all R edges on a tile join (simple junctions).
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                union((cell, edges[i]), (cell, edges[j]))

    for cell, d in nodes:
        nb = neighbor(cell, d)
        if nb is None:
            continue
        other = state.tile_at(nb)
        if other is None:
            continue
        if edge_of(other, OPP[d]) == "R":
            union((cell, d), (nb, OPP[d]))

    groups: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for n in nodes:
        groups.setdefault(find(n), set()).add(n)
    return list(groups.values())


def feature_open(state: State, nodes: set[tuple[str, str]]) -> bool:
    """Open when any edge faces empty board space or the outer rim."""
    for cell, d in nodes:
        nb = neighbor(cell, d)
        if nb is None:
            return True  # rim stays open
        if state.tile_at(nb) is None:
            return True
    return False


def farm_region(state: State, cell: str, edge: str) -> set[tuple[str, str]]:
    tile = state.tile_at(cell)
    if tile is None or edge not in DIRS or edge_of(tile, edge) != "F":
        return set()
    nodes: list[tuple[str, str]] = []
    for c in CELLS:
        t = state.tile_at(c)
        if t is None:
            continue
        for d in DIRS:
            if edge_of(t, d) == "F":
                nodes.append((c, d))
    parent = {n: n for n in nodes}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_cell: dict[str, list[str]] = {}
    for c, d in nodes:
        by_cell.setdefault(c, []).append(d)
    for c, edges in by_cell.items():
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                # F edges on a tile join unless separated by R/C — house: all F join
                union((c, edges[i]), (c, edges[j]))
    for c, d in nodes:
        nb = neighbor(c, d)
        if nb is None:
            continue
        other = state.tile_at(nb)
        if other is None:
            continue
        if edge_of(other, OPP[d]) == "F":
            union((c, d), (nb, OPP[d]))

    root = find((cell, edge))
    return {n for n in nodes if find(n) == root}


def meeples_on_nodes(
    state: State, kind: str, nodes: set[tuple[str, str]]
) -> list[Meeple]:
    out = []
    for cell, m in state.meeples:
        if m.kind != kind:
            continue
        if kind == "cloister":
            # cloister meeple sits on cell with C edge marker
            if any(c == cell for c, _ in nodes):
                out.append(m)
            continue
        if (cell, m.edge) in nodes:
            out.append(m)
    return out


def cloister_complete(state: State, cell: str) -> bool:
    tile = state.tile_at(cell)
    if tile is None or not tile.cloister:
        return False
    x, y = cell_xy(cell)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nb = xy_cell(x + dx, y + dy)
            if nb is None:
                continue  # off-board neighbor not required
            if state.tile_at(nb) is None:
                return False
    return True


def city_tiles(nodes: set[tuple[str, str]]) -> set[str]:
    return {c for c, _ in nodes}


def score_completed_features(state: State) -> tuple[State, int]:
    """Score newly completed uncontested Red features; return (new_state, delta)."""
    delta = 0
    remaining = list(state.meeples)
    scored_city_ids: list[frozenset[str]] = list(state.completed_cities)

    # Cities
    for comp in city_components(state):
        if feature_open(state, comp):
            continue
        tileset = frozenset(city_tiles(comp))
        if tileset in scored_city_ids:
            continue
        owners = meeples_on_nodes(state, "city", comp)
        pennants = sum(
            1
            for c in tileset
            if (t := state.tile_at(c)) is not None and t.pennant
        )
        red_sole = bool(owners) and all(o.colour == RED for o in owners)
        if red_sole:
            delta += 2 * len(tileset) + 2 * pennants
            scored_city_ids.append(tileset)
        # Contested or empty cities complete without feeding the Red farm ledger.
        # remove meeples on this feature
        remaining = [
            (c, m)
            for c, m in remaining
            if not (m.kind == "city" and (c, m.edge) in comp)
        ]

    # Roads
    for comp in road_components(state):
        if feature_open(state, comp):
            continue
        owners = meeples_on_nodes(state, "road", comp)
        if owners and all(o.colour == RED for o in owners):
            delta += len(city_tiles(comp))
        remaining = [
            (c, m)
            for c, m in remaining
            if not (m.kind == "road" and (c, m.edge) in comp)
        ]

    # Cloisters
    for cell in CELLS:
        tile = state.tile_at(cell)
        if tile is None or not tile.cloister:
            continue
        if not cloister_complete(state, cell):
            continue
        owners = [m for c, m in remaining if c == cell and m.kind == "cloister"]
        if owners and all(o.colour == RED for o in owners):
            # 1 + occupied neighbors (including only on-board)
            x, y = cell_xy(cell)
            neigh = 0
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nb = xy_cell(x + dx, y + dy)
                    if nb is not None and state.tile_at(nb) is not None:
                        neigh += 1
            delta += 1 + neigh
        remaining = [
            (c, m)
            for c, m in remaining
            if not (c == cell and m.kind == "cloister")
        ]

    # Farmer majority: each sole-Red farm scores 3 per completed city it touches.
    completed = scored_city_ids
    farm_seen: set[frozenset[tuple[str, str]]] = set()
    for cell, m in list(remaining):
        if m.kind != "farm" or m.colour != RED:
            continue
        region = farm_region(state, cell, m.edge)
        key = frozenset(region)
        if not region or key in farm_seen:
            continue
        farm_seen.add(key)
        # contested?
        blue_here = False
        for c2, m2 in remaining:
            if m2.kind != "farm" or m2.colour != BLUE:
                continue
            if (c2, m2.edge) in region:
                blue_here = True
                break
        if blue_here:
            continue
        region_cells = {c for c, _ in region}
        touched = 0
        for city in completed:
            # touches if city tile orthogonally/same as any farm-region tile
            for ct in city:
                if ct in region_cells:
                    touched += 1
                    break
                x, y = cell_xy(ct)
                for d in DIRS:
                    nb = neighbor(ct, d)
                    if nb is not None and nb in region_cells:
                        touched += 1
                        break
                else:
                    continue
                break
        delta += 3 * touched

    new_state = replace(
        state,
        meeples=tuple(remaining),
        score=state.score + delta,
        completed_cities=tuple(scored_city_ids),
    )
    return new_state, delta


def parse_red_move(text: str) -> tuple[str, str, int, Meeple | None]:
    """Parse `CFRF@b2:0+city:N` or `CFRF@b2:0` → code, cell, rot, meeple?"""
    if "+" in text:
        base, seat = text.split("+", 1)
        kind, edge = seat.split(":")
        meeple = Meeple(RED, kind, edge)
    else:
        base = text
        meeple = None
    code, at = base.split("@", 1)
    cell, rot_s = at.split(":")
    return code, cell, int(rot_s), meeple


def fmt_red_move(code: str, cell: str, rot: int, meeple: Meeple | None) -> str:
    body = f"{code}@{cell}:{rot}"
    if meeple is None:
        return body
    return f"{body}+{meeple.kind}:{meeple.edge}"


def parse_blue_move(text: str) -> tuple[str, ...] | None:
    if text == "pass":
        return None
    # seat:b2:city:N
    _seat, cell, kind, edge = text.split(":")
    return (cell, kind, edge)


def fmt_blue_seat(cell: str, kind: str, edge: str) -> str:
    return f"seat:{cell}:{kind}:{edge}"


def apply_red(state: State, move: str) -> State:
    code, cell, rot, meeple = parse_red_move(move)
    if code not in state.hand:
        raise ValueError(f"tile not in hand: {code}")
    edges, cloister, pennant = parse_tile_code(code)
    tile = Tile(rotate_edges(edges, rot), cloister, pennant)
    if not placement_legal(state, cell, tile):
        raise ValueError(f"illegal placement {move}")
    if meeple is not None:
        if meeple.kind == "cloister":
            if not tile.cloister or meeple.edge != "C":
                raise ValueError("bad cloister seat")
        elif meeple.edge not in DIRS:
            raise ValueError("bad seat edge")
        elif meeple.kind == "city" and edge_of(tile, meeple.edge) != "C":
            raise ValueError("city seat mismatch")
        elif meeple.kind == "road" and edge_of(tile, meeple.edge) != "R":
            raise ValueError("road seat mismatch")
        elif meeple.kind == "farm" and edge_of(tile, meeple.edge) != "F":
            raise ValueError("farm seat mismatch")
    hand = list(state.hand)
    hand.remove(code)
    st = state.with_tile(cell, tile)
    st = replace(st, hand=tuple(hand))
    if meeple is not None:
        st = st.add_meeple(cell, meeple)
    st, _ = score_completed_features(st)
    return st


def apply_blue(state: State, move: str) -> State:
    parsed = parse_blue_move(move)
    if parsed is None:
        return state
    if state.blue_stock <= 0:
        raise ValueError("no blue stock")
    cell, kind, edge = parsed
    tile = state.tile_at(cell)
    if tile is None:
        raise ValueError("seat on empty")
    if kind == "cloister":
        if not tile.cloister or edge != "C":
            raise ValueError("bad cloister")
    elif kind == "city" and edge_of(tile, edge) != "C":
        raise ValueError("bad city seat")
    elif kind == "road" and edge_of(tile, edge) != "R":
        raise ValueError("bad road seat")
    elif kind == "farm" and edge_of(tile, edge) != "F":
        raise ValueError("bad farm seat")
    # cannot seat on already occupied exact seat
    for c, m in state.meeples:
        if c == cell and m.kind == kind and m.edge == edge:
            raise ValueError("occupied")
    st = state.add_meeple(cell, Meeple(BLUE, kind, edge))
    st = replace(st, blue_stock=state.blue_stock - 1)
    st, _ = score_completed_features(st)
    return st


def legal_red_moves(state: State) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for code in state.hand:
        edges0, cloister, pennant = parse_tile_code(code)
        # House rule: hand codes are pre-oriented; no rotation at the table.
        rot = 0
        tile = Tile(edges0, cloister, pennant)
        for cell in CELLS:
            if not placement_legal(state, cell, tile):
                continue
            mv = fmt_red_move(code, cell, rot, None)
            if mv not in seen:
                seen.add(mv)
                out.append(mv)
            seats: list[Meeple] = []
            for d in DIRS:
                e = edge_of(tile, d)
                if e == "C":
                    seats.append(Meeple(RED, "city", d))
                elif e == "R":
                    seats.append(Meeple(RED, "road", d))
                elif e == "F":
                    seats.append(Meeple(RED, "farm", d))
            if tile.cloister:
                seats.append(Meeple(RED, "cloister", "C"))
            for m in seats:
                mv = fmt_red_move(code, cell, rot, m)
                if mv not in seen:
                    seen.add(mv)
                    out.append(mv)
    return out


def legal_blue_moves(state: State) -> list[str]:
    moves = ["pass"]
    if state.blue_stock <= 0:
        return moves
    seen: set[str] = set()
    for cell in CELLS:
        tile = state.tile_at(cell)
        if tile is None:
            continue
        candidates: list[tuple[str, str]] = []
        for d in DIRS:
            e = edge_of(tile, d)
            if e == "C":
                candidates.append(("city", d))
            elif e == "R":
                candidates.append(("road", d))
            elif e == "F":
                candidates.append(("farm", d))
        if tile.cloister:
            candidates.append(("cloister", "C"))
        for kind, edge in candidates:
            occupied = any(
                c == cell and m.kind == kind and m.edge == edge
                for c, m in state.meeples
            )
            if occupied:
                continue
            mv = fmt_blue_seat(cell, kind, edge)
            if mv not in seen:
                seen.add(mv)
                moves.append(mv)
    return moves


def goal_met(state: State) -> bool:
    return state.score >= state.floor


def can_coop(state: State, stones: int | None = None) -> bool:
    left = state.budget if stones is None else stones

    def dfs(st: State, rem: int) -> bool:
        if goal_met(st):
            return True
        if rem <= 0 or not st.hand:
            return False
        for mv in legal_red_moves(st):
            try:
                nxt = apply_red(st, mv)
            except ValueError:
                continue
            if dfs(nxt, rem - 1):
                return True
        return False

    return dfs(state, left)


def can_force(state: State, stones: int | None = None) -> bool:
    left = state.budget if stones is None else stones

    def red_turn(st: State, rem: int) -> bool:
        if goal_met(st):
            return True
        if rem <= 0 or not st.hand:
            return False
        for mv in legal_red_moves(st):
            try:
                nxt = apply_red(st, mv)
            except ValueError:
                continue
            if goal_met(nxt):
                return True
            if blue_turn(nxt, rem - 1):
                return True
        return False

    def blue_turn(st: State, rem: int) -> bool:
        if goal_met(st):
            return True
        if rem <= 0:
            return False
        replies = legal_blue_moves(st)
        # Blue fights: Red forces only if EVERY reply still loses for Blue
        for mv in replies:
            try:
                nxt = apply_blue(st, mv)
            except ValueError:
                continue
            if not red_turn(nxt, rem):
                return False
        return True

    return red_turn(state, left)


def verdict(state: State) -> str:
    if can_force(state):
        return "win"
    if can_coop(state):
        return "trap"
    return "fort"


def find_coop_line(state: State) -> list[str] | None:
    def dfs(st: State, rem: int, path: list[str]) -> list[str] | None:
        if goal_met(st):
            return path
        if rem <= 0 or not st.hand:
            return None
        for mv in legal_red_moves(st):
            try:
                nxt = apply_red(st, mv)
            except ValueError:
                continue
            got = dfs(nxt, rem - 1, path + [f"red {mv}"])
            if got is not None:
                return got
        return None

    return dfs(state, state.budget, [])


def find_force_line(state: State) -> list[str] | None:
    def red_turn(st: State, rem: int, path: list[str]) -> list[str] | None:
        if goal_met(st):
            return path
        if rem <= 0 or not st.hand:
            return None
        for mv in legal_red_moves(st):
            try:
                nxt = apply_red(st, mv)
            except ValueError:
                continue
            step = path + [f"red {mv}"]
            if goal_met(nxt):
                return step
            got = blue_turn(nxt, rem - 1, step)
            if got is not None:
                return got
        return None

    def blue_turn(st: State, rem: int, path: list[str]) -> list[str] | None:
        if goal_met(st):
            return path
        if rem <= 0:
            return None
        replies = legal_blue_moves(st)
        # Pick any reply that still allows a force; for PV we need a line that
        # works against ALL — build by requiring each branch works and record
        # the pass-preferring reply when multiple.
        # For a concrete PV against adversarial Blue, we need the line to
        # specify Blue's actual replies. Store one forcing tree path preferring
        # the lexicographically first reply that fails Blue (i.e. still forced).
        # Actually: for each Red move we need that for ALL blue replies, Red
        # still forces. The PV picks, at each Blue node, an arbitrary reply
        # (lex smallest) and continues — tests check forcing against ALL.
        ordered = sorted(replies)
        # Verify all replies still force; then extend along first reply.
        branches: list[tuple[str, State]] = []
        for mv in ordered:
            try:
                nxt = apply_blue(st, mv)
            except ValueError:
                continue
            branches.append((mv, nxt))
        if not branches:
            return red_turn(st, rem, path)
        for mv, nxt in branches:
            if not can_force(nxt, rem):
                return None
        mv0, nxt0 = branches[0]
        return red_turn(nxt0, rem, path + [f"blue {mv0}"])

    return red_turn(state, state.budget, [])


def threats(state: State) -> list[str]:
    """Red first moves that do not meet the floor but would on the next Red turn if Blue passes."""
    out = []
    for mv in legal_red_moves(state):
        try:
            after = apply_red(state, mv)
        except ValueError:
            continue
        if goal_met(after):
            continue
        # Would meet on a single further Red turn with Blue pass
        meets = False
        for mv2 in legal_red_moves(after):
            try:
                nxt = apply_red(after, mv2)
            except ValueError:
                continue
            if goal_met(nxt):
                meets = True
                break
        if meets:
            out.append(mv)
    return out


def forcing_first_moves(state: State) -> list[str]:
    """Red first placements that begin a forcing win."""
    out: list[str] = []
    for mv in legal_red_moves(state):
        try:
            after = apply_red(state, mv)
        except ValueError:
            continue
        if goal_met(after):
            out.append(mv)
            continue
        if all(
            can_force(apply_blue(after, reply), state.budget - 1)
            for reply in legal_blue_moves(after)
        ):
            out.append(mv)
    return out


def find_refutation(state: State, threat: str) -> str | None:
    after = apply_red(state, threat)
    for reply in legal_blue_moves(after):
        try:
            held = apply_blue(after, reply)
        except ValueError:
            continue
        if any(
            goal_met(apply_red(held, mv2))
            for mv2 in legal_red_moves(held)
            if True
        ):
            # still can finish next turn — not a refutation
            # need: after reply, Red cannot meet on following single turn
            pass
        can_finish = False
        for mv2 in legal_red_moves(held):
            try:
                if goal_met(apply_red(held, mv2)):
                    can_finish = True
                    break
            except ValueError:
                continue
        if not can_finish:
            return reply
    return None


def board_id_of(text: str, path_stem: str = "") -> str:
    for line in text.splitlines():
        if line.startswith("board_id:"):
            return line.split(":", 1)[1].strip()
    return path_stem.replace("board_", "")


CARD = Path("/app/answers.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
JUDGE_LIVE = Path("/app/bin/judge.jar")
BUDGET = 3
VERDICTS = ("win", "trap", "fort")
SCHEMA = "carcassonne-meeple-v1"


@cache
def sheets() -> dict[str, tuple[object, Path]]:
    out: dict[str, tuple[object, Path]] = {}
    for path in sorted(SHEETS.glob("board_*.txt")):
        text = path.read_text()
        st = parse_sheet(text)
        board_id = ""
        for line in text.splitlines():
            if line.startswith("board_id:"):
                board_id = line.split(":", 1)[1].strip()
                break
        if not board_id:
            board_id = path.stem.replace("board_", "")
        out[board_id] = (st, path)
    return out


def card_rounds() -> dict[str, dict]:
    assert CARD.is_file() and CARD.stat().st_size > 0, "tournament card missing"
    body = json.loads(CARD.read_text())
    assert body.get("schema_tag") == SCHEMA
    rounds = body.get("rounds")
    assert isinstance(rounds, list)
    return {row["board_id"]: row for row in rounds if isinstance(row, dict)}


def judge_line(path: Path, steps: list[str]) -> dict:
    out = subprocess.run(
        [
            "java",
            "-jar",
            str(JUDGE),
            "validate",
            "--board",
            str(path),
            "--line",
            ";".join(steps),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def parse_step(st, step: str):
    colour, move = step.split(" ", 1)
    return colour, move


def forcing_ok(st, sequence: list[str]) -> bool:
    if not sequence:
        return False
    cur = st
    stones = BUDGET
    who = "red"
    for step in sequence:
        colour, move = parse_step(cur, step)
        if colour != who:
            return False
        if who == "red":
            if stones <= 0:
                return False
            if move not in legal_red_moves(cur):
                return False
            after = apply_red(cur, move)
            stones -= 1
            if goal_met(after):
                return True
            replies = legal_blue_moves(after)
            if replies:
                if not all(
                    can_force(apply_blue(after, reply), stones) for reply in replies
                ):
                    return False
            elif not can_force(after, stones):
                return False
            cur = after
            who = "blue"
        else:
            if move not in legal_blue_moves(cur):
                return False
            cur = apply_blue(cur, move)
            if goal_met(cur):
                return True
            who = "red"
    return goal_met(cur)


def friendly_ok(st, sequence: list[str]) -> bool:
    if not sequence or len(sequence) > BUDGET:
        return False
    cur = st
    for step in sequence:
        colour, move = parse_step(cur, step)
        if colour != "red":
            return False
        if move not in legal_red_moves(cur):
            return False
        cur = apply_red(cur, move)
        if goal_met(cur):
            return True
    return False


def refutations_ok(st, rows: list) -> bool:
    wanted = set(threats(st))
    if not wanted:
        return False
    filed: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            return False
        placement, reply = row.get("placement"), row.get("reply")
        if not isinstance(placement, str) or not isinstance(reply, str):
            return False
        if placement in filed:
            return False
        filed[placement] = reply
    if not wanted.issubset(set(filed)):
        return False
    for placement, reply in filed.items():
        try:
            after = apply_red(st, placement)
        except ValueError:
            return False
        if goal_met(after):
            return False
        if reply not in legal_blue_moves(after):
            return False
        held = apply_blue(after, reply)
        if any(
            goal_met(apply_red(held, mv2))
            for mv2 in legal_red_moves(held)
        ):
            return False
    return True


def round_ok(board_id: str, row: dict) -> bool:
    st, path = sheets()[board_id]
    want = verdict(st)
    if row.get("status") != want:
        return False
    if bool(row.get("coop_claim")) != (want != "fort"):
        return False
    sequence = row.get("sequence")
    if not isinstance(sequence, list):
        return False
    refutations = row.get("refutations")
    if not isinstance(refutations, list):
        return False
    tile = row.get("tile")
    meeple = row.get("meeple")
    score_delta = row.get("score_delta")
    if want == "fort":
        return (
            sequence == []
            and refutations == []
            and tile == ""
            and meeple == ""
            and score_delta == 0
        )
    if not isinstance(tile, str) or not isinstance(meeple, str):
        return False
    if not isinstance(score_delta, int):
        return False
    if want == "win":
        if refutations:
            return False
        if not sequence or not isinstance(sequence[0], str):
            return False
        first = sequence[0].split(" ", 1)[1]
        if first.split("+", 1)[0] != tile:
            return False
        _c, _cell, _rot, m = parse_red_move(first)
        seat = "" if m is None else f"{m.kind}:{m.edge}"
        if seat != meeple:
            return False
        if first not in forcing_first_moves(st):
            return False
        if not forcing_ok(st, [str(s) for s in sequence]):
            return False
        seen = judge_line(path, [str(s) for s in sequence])
        return (
            seen["all_legal"]
            and seen["enclosed"]
            and seen["score"] == score_delta
            and seen["red_turns"] <= BUDGET
        )
    if not friendly_ok(st, [str(s) for s in sequence]):
        return False
    if not refutations_ok(st, refutations):
        return False
    first = sequence[0].split(" ", 1)[1]
    if first.split("+", 1)[0] != tile:
        return False
    seen = judge_line(path, [str(s) for s in sequence])
    return (
        seen["all_legal"]
        and seen["enclosed"]
        and seen["score"] == score_delta
        and seen["red_turns"] <= BUDGET
        and sequence
        and sequence[0] == f"red {first}"
    )


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Eleven rounds, house verdict words, schema tag, ordered board ids."""
    rounds = card_rounds()
    assert set(rounds) == set(sheets()), (
        f"card covers {sorted(rounds)}; booklet has {sorted(sheets())}"
    )
    body = json.loads(CARD.read_text())
    ids = [r["board_id"] for r in body["rounds"]]
    assert ids == sorted(ids), "rounds must be ordered by board_id"
    for board_id, row in rounds.items():
        status = row.get("status")
        assert status in VERDICTS, f"round {board_id} status {status!r}"
        assert isinstance(row.get("sequence"), list)
        assert isinstance(row.get("refutations"), list)
        assert isinstance(row.get("coop_claim"), bool)
        if status == "fort":
            assert row["sequence"] == []
            assert row["tile"] == ""
        else:
            assert row["sequence"]
            assert row["tile"]
        if status != "trap":
            assert row["refutations"] == []
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_sequences_replay_past_the_sealed_judge():
    """The table replays every sequence: legal turns, floor met, score matches."""
    assert JUDGE_LIVE.is_file(), "the sealed judge left the table"
    assert JUDGE_LIVE.read_bytes() == JUDGE.read_bytes(), "the sealed judge was altered"
    rounds = card_rounds()
    carried = [
        (board_id, row)
        for board_id, row in sorted(rounds.items())
        if isinstance(row.get("sequence"), list) and row["sequence"]
    ]
    assert len(carried) >= 7, f"only {len(carried)} rounds carry a sequence"
    ok = 0
    for board_id, row in carried:
        _, path = sheets()[board_id]
        steps = [str(s) for s in row["sequence"]]
        try:
            seen = judge_line(path, steps)
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if (
            seen["all_legal"]
            and seen["enclosed"]
            and seen["score"] == row.get("score_delta")
            and seen["red_turns"] <= BUDGET
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed sequences"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (st, _) in sorted(sheets().items()):
        row = rounds.get(board_id, {})
        if row.get("status") == verdict(st) and bool(row.get("coop_claim")) == (
            verdict(st) != "fort"
        ):
            ok += 1
    assert ok >= 10, f"verdicts agree on {ok}/11 rounds"


def test_g2_flint_forcing_sequences_really_force():
    """A win sequence has to hold up against every Blue reply, not a soft one."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "win"
    ]
    ok = 0
    for board_id in wanted:
        st, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "win":
            continue
        sequence = row.get("sequence")
        if not isinstance(sequence, list) or not sequence:
            continue
        first = str(sequence[0]).split(" ", 1)[1]
        try:
            if first in forcing_first_moves(st) and forcing_ok(
                st, [str(s) for s in sequence]
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win sequences force the floor"


def test_j4_amber_friendly_sequences_reach_the_floor():
    """Trap sequences are Red alone inside three turns with Blue sitting still."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        st, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "trap":
            continue
        sequence = row.get("sequence")
        if not isinstance(sequence, list):
            continue
        try:
            if friendly_ok(st, [str(s) for s in sequence]):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} friendly sequences reach the floor"


def test_k7_topaz_refutations_cover_every_threat():
    """Blue must answer each contested first claim; coverage is required ⊆ filed."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        st, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        rows = row.get("refutations")
        if row.get("status") != "trap" or not isinstance(rows, list):
            continue
        try:
            if refutations_ok(st, rows):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap rounds fully refuted"


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """The kiosk stamps a win wherever a fourth turn reaches; the table does not."""
    rounds = card_rounds()
    forts = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "fort"
    ]
    assert forts, "booklet lost its fort rounds"
    held = sum(1 for board_id in forts if rounds.get(board_id, {}).get("status") == "fort")
    assert held >= len(forts) - 1, f"{held}/{len(forts)} fort rounds filed as forts"
    optimistic = sum(1 for row in rounds.values() if row.get("status") == "win")
    assert optimistic < len(rounds), "every round filed as a win"
    for board_id in forts:
        st, _ = sheets()[board_id]
        assert can_coop(st, 4), f"fort {board_id} is not fourth-turn coop bait"
        assert not can_force(st)


def test_n2_coral_score_delta_is_not_padded():
    """Filed score_delta must match the sealed judge after the sequence."""
    rounds = card_rounds()
    ok = 0
    checked = 0
    for board_id, row in sorted(rounds.items()):
        sequence = row.get("sequence")
        if not isinstance(sequence, list) or not sequence:
            continue
        checked += 1
        _, path = sheets()[board_id]
        try:
            seen = judge_line(path, [str(s) for s in sequence])
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if seen.get("score") == row.get("score_delta") and seen.get("enclosed"):
            ok += 1
    assert checked >= 7
    assert ok >= checked - 1, f"score_delta matched on {ok}/{checked} sequenced rounds"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, play, refutations, and score together."""
    rounds = card_rounds()
    ok = 0
    for board_id in sorted(sheets()):
        row = rounds.get(board_id)
        if not isinstance(row, dict):
            continue
        try:
            if round_ok(board_id, row):
                ok += 1
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
    assert ok >= 10, f"{ok}/11 rounds stand up end to end"


def test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card(tmp_path):
    """A finished card must come out the same bytes when the desk emits twice."""
    assert CARD.is_file() and CARD.stat().st_size > 0
    staged = tmp_path / "answers.json"
    staged.write_bytes(CARD.read_bytes())
    command = ["bash", "/app/kiosk/emit_card.sh", str(staged)]
    first_run = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    assert first_run.returncode == 0, first_run.stderr
    first = staged.read_bytes()
    second_run = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    assert second_run.returncode == 0, second_run.stderr
    assert first == staged.read_bytes()
    assert first == CARD.read_bytes()
