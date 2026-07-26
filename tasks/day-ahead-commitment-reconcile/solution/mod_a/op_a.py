"""Opaque helper — marginal token recovery."""


def op_a(a, b):
    """Return highest offer among positive assignments in mapping b using row table a."""
    idx = {r[0]: r for r in a}
    offers = []
    for uid, mw in b.items():
        if mw > 0:
            offers.append(idx[uid][2])
    if not offers:
        raise ValueError("empty")
    return max(offers)


def binds_flag(a, b, need):
    idx = {r[0]: r for r in a}
    room = 0
    for uid, mw in b.items():
        if mw > 0:
            room += idx[uid][1] - mw
    return room == need
