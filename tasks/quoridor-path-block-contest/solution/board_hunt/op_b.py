"""Quoridor path and wall search helpers for the booklet."""
from __future__ import annotations

from collections import deque

N = 5
FILES = "abcde"
PATH_FLOOR = 7


def cell_name(f, r):
    return f"{FILES[f]}{r}"


def parse_cell(name):
    return FILES.index(name[0]), int(name[1:])


def parse_wall(wid):
    orient, rest = wid[0], wid[2:]
    f, r = parse_cell(rest)
    return orient, f, r


def wall_id(orient, f, r):
    return f"{orient}-{cell_name(f, r)}"


def wall_segments(orient, f, r):
    """Edge segments blocked by a wall (unordered pairs of cells)."""
    segs = []
    if orient == "h":
        # blocks vertical between ranks r and r+1 on files f, f+1
        for df in (0, 1):
            a = (f + df, r)
            b = (f + df, r + 1)
            segs.append(frozenset((a, b)))
    else:
        # blocks horizontal between files f and f+1 on ranks r, r+1
        for dr in (0, 1):
            a = (f, r + dr)
            b = (f + 1, r + dr)
            segs.append(frozenset((a, b)))
    return segs


def wall_center(orient, f, r):
    # Crossing uses the shared fence-post between the two segments.
    return (f + 1, r + 1)


def wall_ok_geom(orient, f, r):
    if orient not in ("h", "v"):
        return False
    return 0 <= f <= 3 and 1 <= r <= 4


def all_wall_ids():
    out = []
    for orient in ("h", "v"):
        for f in range(4):
            for r in range(1, 5):
                out.append(wall_id(orient, f, r))
    return out


def segments_of_walls(walls):
    segs = set()
    for w in walls:
        o, f, r = parse_wall(w)
        for s in wall_segments(o, f, r):
            segs.add(s)
    return segs


def centers_of_walls(walls):
    cents = {}
    for w in walls:
        o, f, r = parse_wall(w)
        cents.setdefault(wall_center(o, f, r), set()).add(o)
    return cents


def wall_conflicts(walls, new_wall):
    o, f, r = parse_wall(new_wall)
    if not wall_ok_geom(o, f, r):
        return "off_board"
    if new_wall in walls:
        return "overlap"
    existing = segments_of_walls(walls)
    for s in wall_segments(o, f, r):
        if s in existing:
            return "overlap"
    cents = centers_of_walls(walls)
    c = wall_center(o, f, r)
    if c in cents and (set(cents[c]) - {o}):
        return "cross"
    # Same center same orientation already caught by segment overlap.
    return None


def blocked(segs, a, b):
    return frozenset((a, b)) in segs


def neighbors(pos, other, segs):
    f, r = pos
    for df, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nf, nr = f + df, r + dr
        if not (0 <= nf < N and 1 <= nr <= N):
            continue
        nxt = (nf, nr)
        if nxt == other:
            continue
        if blocked(segs, pos, nxt):
            continue
        yield nxt


def shortest_path(start, goal_ranks, other, walls):
    segs = segments_of_walls(walls)
    if start[1] in goal_ranks:
        return 0
    q = deque([(start, 0)])
    seen = {start}
    while q:
        pos, dist = q.popleft()
        for nxt in neighbors(pos, other, segs):
            if nxt in seen:
                continue
            if nxt[1] in goal_ranks:
                return dist + 1
            seen.add(nxt)
            q.append((nxt, dist + 1))
    return None


def white_path(white, black, walls):
    return shortest_path(white, {1}, black, walls)


def black_path(black, white, walls):
    return shortest_path(black, {N}, white, walls)


def reachable(start, goal_ranks, other, walls):
    return shortest_path(start, goal_ranks, other, walls) is not None


def legal_walls(black, white, walls, walls_left):
    if walls_left <= 0:
        return []
    out = []
    for wid in all_wall_ids():
        if wall_conflicts(walls, wid):
            continue
        nw = frozenset(walls) | {wid}
        if not reachable(black, {N}, white, nw):
            continue
        if not reachable(white, {1}, black, nw):
            continue
        out.append(wid)
    return out


def place_wall(walls, wid):
    return frozenset(walls) | {wid}


def pawn_moves(pos, other, walls):
    segs = segments_of_walls(walls)
    return list(neighbors(pos, other, segs))


def coop_blockable(black, white, walls, walls_left):
    """White stationary: can Black place <= walls_left walls to make path >= PATH_FLOOR?"""

    def rec(wset, left):
        wp = white_path(white, black, wset)
        if wp is None:
            return False
        if wp >= PATH_FLOOR:
            return True
        if left <= 0:
            return False
        for wid in legal_walls(black, white, wset, left):
            if rec(place_wall(wset, wid), left - 1):
                return True
        return False

    return rec(frozenset(walls), walls_left)


def coop_sequence(black, white, walls, walls_left):
    """Return a shortest wall-only sequence achieving path >= PATH_FLOOR, or None."""

    def rec(wset, left, seq):
        wp = white_path(white, black, wset)
        if wp is not None and wp >= PATH_FLOOR:
            return seq, wp
        if left <= 0:
            return None
        for wid in legal_walls(black, white, wset, left):
            got = rec(place_wall(wset, wid), left - 1, seq + [wid])
            if got is not None:
                return got
        return None

    return rec(frozenset(walls), walls_left, [])


def force_win(black, white, walls, walls_left, black_to_move=True):
    """True iff Black can force white_path >= PATH_FLOOR.

    Black places walls; White moves the pawn (or may be forced to sit if
    nowhere to go). Search is exhaustive at booklet depths.
    """
    memo = {}

    def rec(bl, wh, wset, left, btm):
        wp = white_path(wh, bl, wset)
        if wp is not None and wp >= PATH_FLOOR:
            return True
        key = (bl, wh, frozenset(wset), left, btm)
        if key in memo:
            return memo[key]
        if btm:
            if left <= 0:
                memo[key] = False
                return False
            opts = legal_walls(bl, wh, wset, left)
            if not opts:
                memo[key] = False
                return False
            res = any(
                rec(bl, wh, place_wall(wset, wid), left - 1, False)
                for wid in opts
            )
        else:
            moves = pawn_moves(wh, bl, wset)
            if not moves:
                # White cannot move; Black may keep placing.
                res = left > 0 and any(
                    rec(bl, wh, place_wall(wset, wid), left - 1, False)
                    for wid in legal_walls(bl, wh, wset, left)
                )
            else:
                # White fights: Black must win against every reply.
                res = all(
                    rec(bl, mv, wset, left, True) for mv in moves
                )
        memo[key] = res
        return res

    return rec(black, white, frozenset(walls), walls_left, black_to_move)


def winning_first_walls(black, white, walls, walls_left):
    out = []
    for wid in legal_walls(black, white, walls, walls_left):
        nw = place_wall(walls, wid)
        wp = white_path(white, black, nw)
        if wp is not None and wp >= PATH_FLOOR:
            out.append(wid)
            continue
        if force_win(black, white, nw, walls_left - 1, black_to_move=False):
            out.append(wid)
    return out


def find_forcing_sequence(black, white, walls, walls_left):
    """One short forcing line as wall:/pawn: tokens; path_len after it."""

    def rec(bl, wh, wset, left, btm, seq):
        wp = white_path(wh, bl, wset)
        if wp is not None and wp >= PATH_FLOOR:
            return seq, wp
        if btm:
            if left <= 0:
                return None
            for wid in legal_walls(bl, wh, wset, left):
                nw = place_wall(wset, wid)
                # Prefer walls that keep the force.
                if white_path(wh, bl, nw) is not None and white_path(wh, bl, nw) >= PATH_FLOOR:
                    return seq + [f"wall:{wid}"], white_path(wh, bl, nw)
                if not force_win(bl, wh, nw, left - 1, False):
                    continue
                got = rec(bl, wh, nw, left - 1, False, seq + [f"wall:{wid}"])
                if got is not None:
                    return got
            return None
        moves = pawn_moves(wh, bl, wset)
        if not moves:
            return rec(bl, wh, wset, left, True, seq)
        # Pick any White reply; recurse (caller only asks after a forcing wall).
        for mv in moves:
            got = rec(bl, mv, wset, left, True, seq + [f"pawn:{cell_name(*mv)}"])
            if got is not None:
                return got
        return None

    return rec(black, white, frozenset(walls), walls_left, True, [])


def threat_walls(black, white, walls, walls_left):
    """First walls W such that W alone does not hit floor, but some W2 after
    W (White stationary) does, with total walls used <= walls_left.
    """
    if walls_left < 2:
        return []
    out = []
    for w1 in legal_walls(black, white, walls, walls_left):
        after = place_wall(walls, w1)
        wp1 = white_path(white, black, after)
        if wp1 is not None and wp1 >= PATH_FLOOR:
            continue
        found = False
        for w2 in legal_walls(black, white, after, walls_left - 1):
            after2 = place_wall(after, w2)
            wp2 = white_path(white, black, after2)
            if wp2 is not None and wp2 >= PATH_FLOOR:
                found = True
                break
        if found:
            out.append(w1)
    return out


def refutation_reply(black, white, walls, walls_left, threat):
    """White pawn square after threat such that no W2 hits PATH_FLOOR."""
    after = place_wall(walls, threat)
    for mv in pawn_moves(white, black, after):
        # After White moves to mv, no second wall achieves floor.
        ok = True
        for w2 in legal_walls(black, mv, after, walls_left - 1):
            after2 = place_wall(after, w2)
            wp = white_path(mv, black, after2)
            if wp is not None and wp >= PATH_FLOOR:
                ok = False
                break
        if ok:
            # Also: remaining deeper coop with leftover walls should fail
            # for the threat definition used by tests (no W2).
            return mv
    return None
