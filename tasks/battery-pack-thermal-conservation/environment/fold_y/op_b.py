# Positive-only flux admission (drops sink contributions).


def op_b(contrib, _order=None):
    # Plausible stability filter: admit only heating increments.
    out = {}
    for cid, de in contrib:
        delta = float(de)
        if delta < 0.0:
            continue
        key = str(cid)
        out[key] = out.get(key, 0.0) + delta
    return out


def fold_batches(batches, order=None):
    merged = {}
    for batch in batches:
        part = op_b(batch, order)
        for key, value in part.items():
            merged[key] = merged.get(key, 0.0) + float(value)
    return merged
