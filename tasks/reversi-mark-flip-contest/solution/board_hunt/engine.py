"""Reversi play for the marked-disc booklet: drops, flips, and search."""

from __future__ import annotations

from functools import lru_cache

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
FILES = "abcdefgh"
CORNERS = ("a1", "h1", "a8", "h8")
STONES = 3

DIRS = (
    (1, ~FILE_H & FULL),
    (-1, ~FILE_A & FULL),
    (8, FULL),
    (-8, FULL),
    (9, ~FILE_H & FULL),
    (-9, ~FILE_A & FULL),
    (7, ~FILE_A & FULL),
    (-7, ~FILE_H & FULL),
)


def shift(x: int, step: int, guard: int) -> int:
    x &= guard
    return ((x << step) & FULL) if step > 0 else (x >> -step)


def sq(name: str) -> int:
    return (ord(name[1]) - ord("1")) * 8 + (ord(name[0]) - ord("a"))


def nm(index: int) -> str:
    return f"{FILES[index % 8]}{index // 8 + 1}"


def bits(mask: int):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


@lru_cache(maxsize=1 << 19)
def drops(mine: int, theirs: int) -> int:
    """Every legal drop for the side holding `mine`."""
    empty = FULL & ~(mine | theirs)
    out = 0
    for step, guard in DIRS:
        run = shift(mine, step, guard) & theirs
        for _ in range(5):
            run |= shift(run, step, guard) & theirs
        out |= shift(run, step, guard) & empty
    return out


def turned(mine: int, theirs: int, move: int) -> int:
    """Discs that turn over when `mine` drops on `move`."""
    spot = 1 << move
    if (mine | theirs) & spot:
        return 0
    out = 0
    for step, guard in DIRS:
        run = 0
        walk = shift(spot, step, guard)
        while walk & theirs:
            run |= walk
            walk = shift(walk, step, guard)
        if run and (walk & mine):
            out |= run
    return out


def play(mine: int, theirs: int, move: int):
    flipped = turned(mine, theirs, move)
    if not flipped:
        raise ValueError(f"illegal drop {nm(move)}")
    return mine | flipped | (1 << move), theirs & ~flipped


def announce(mine: int, theirs: int, move: int) -> str:
    tag = f"flips:{turned(mine, theirs, move).bit_count()}"
    return tag + "+corner" if nm(move) in CORNERS else tag


@lru_cache(maxsize=1 << 20)
def forced(black: int, white: int, mark: int, stones: int) -> bool:
    """Black to move: does Black turn the mark inside `stones` however White fights?"""
    if black & mark:
        return True
    if stones <= 0:
        return False
    mine = drops(black, white)
    if not mine:
        theirs = drops(white, black)
        if not theirs:
            return False
        return all(
            forced(*reversed(play(white, black, reply)), mark, stones)
            for reply in bits(theirs)
        )
    for move in bits(mine):
        nb, nw = play(black, white, move)
        if nb & mark:
            return True
        if stones == 1:
            continue
        replies = drops(nw, nb)
        if not replies:
            if forced(nb, nw, mark, stones - 1):
                return True
            continue
        if all(
            forced(*reversed(play(nw, nb, reply)), mark, stones - 1)
            for reply in bits(replies)
        ):
            return True
    return False


@lru_cache(maxsize=1 << 19)
def friendly(black: int, white: int, mark: int, stones: int) -> bool:
    """White passes every turn: does Black turn the mark inside `stones`?"""
    if black & mark:
        return True
    if stones <= 0:
        return False
    for move in bits(drops(black, white)):
        nb, nw = play(black, white, move)
        if (nb & mark) or friendly(nb, nw, mark, stones - 1):
            return True
    return False


def finishers(black: int, white: int, mark: int) -> list[int]:
    """Black drops that turn the mark right now."""
    return [m for m in bits(drops(black, white)) if play(black, white, m)[0] & mark]


def threats(black: int, white: int, mark: int) -> list[int]:
    """Black openers that leave the mark falling to Black's very next drop."""
    out = []
    for move in bits(drops(black, white)):
        nb, nw = play(black, white, move)
        if nb & mark:
            continue
        if finishers(nb, nw, mark):
            out.append(move)
    return sorted(out, key=nm)


def answer_to(black: int, white: int, mark: int, threat: int):
    """A White reply after `threat` leaving no single Black drop on the mark."""
    nb, nw = play(black, white, threat)
    replies = drops(nw, nb)
    if not replies:
        return "pass" if not finishers(nb, nw, mark) else None
    for reply in sorted(bits(replies), key=nm):
        w2, b2 = play(nw, nb, reply)
        if b2 & mark:
            continue
        if not finishers(b2, w2, mark):
            return nm(reply)
    return None


def forcing_line(black: int, white: int, mark: int):
    """Black drops that keep the take forced, with White's stubbornest replies."""
    b, w, stones = black, white, STONES
    line: list[str] = []
    while True:
        if b & mark:
            return line
        mine = drops(b, w)
        if not mine:
            replies = drops(w, b)
            if not replies:
                return None
            line.append("white pass")
            reply = min(bits(replies), key=nm)
            line.append(f"white {nm(reply)}|{announce(w, b, reply)}")
            w, b = play(w, b, reply)
            continue
        picked = None
        for move in sorted(bits(mine), key=nm):
            nb, nw = play(b, w, move)
            if nb & mark:
                picked = move
                break
            if stones == 1:
                continue
            replies = drops(nw, nb)
            if not replies:
                if forced(nb, nw, mark, stones - 1):
                    picked = move
                    break
                continue
            if all(
                forced(*reversed(play(nw, nb, reply)), mark, stones - 1)
                for reply in bits(replies)
            ):
                picked = move
                break
        if picked is None:
            return None
        line.append(f"black {nm(picked)}|{announce(b, w, picked)}")
        b, w = play(b, w, picked)
        stones -= 1
        if b & mark:
            return line
        replies = drops(w, b)
        if not replies:
            line.append("white pass")
            continue
        reply = min(
            bits(replies),
            key=lambda r: (forced(*reversed(play(w, b, r)), mark, stones), nm(r)),
        )
        line.append(f"white {nm(reply)}|{announce(w, b, reply)}")
        w, b = play(w, b, reply)


def friendly_line(black: int, white: int, mark: int, stones: int = STONES):
    """Black-only drops that reach the mark while White sits still."""
    for move in sorted(bits(drops(black, white)), key=nm):
        nb, nw = play(black, white, move)
        step = f"black {nm(move)}|{announce(black, white, move)}"
        if nb & mark:
            return [step]
        if stones > 1:
            rest = friendly_line(nb, nw, mark, stones - 1)
            if rest is not None:
                return [step] + rest
    return None
