"""Carcassonne house-rules engine for the tile-meeple booklet.

Shared by the oracle search and (conceptually) the sealed table judge.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

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
