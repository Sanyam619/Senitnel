# Compensated accumulation of pairwise heat increments.


def op_b(contrib, _order=None):
    acc = {}
    carry = {}
    for cid, de in contrib:
        key = str(cid)
        delta = float(de)
        y = delta - carry.get(key, 0.0)
        prior = acc.get(key, 0.0)
        nxt = prior + y
        carry[key] = (nxt - prior) - y
        acc[key] = nxt
    return acc


def _merge_partial(left, right):
    out = dict(left)
    for key, value in right.items():
        out[key] = out.get(key, 0.0) + float(value)
    return out


def fold_batches(batches, order=None):
    merged = {}
    for batch in batches:
        merged = _merge_partial(merged, op_b(batch, order))
    return merged
