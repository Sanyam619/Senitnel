# Contact scale lookup for linked faces.


def op_a(material, _policy=None):
    table = {
        "gap": 0.4,
        "weld": 1.0,
        "paste": 0.7,
        "foam": 0.25,
        "film": 0.55,
    }
    key = str(material).strip().lower()
    if key in table:
        return float(table[key])
    return 1.0


def _validate_scale(value):
    v = float(value)
    if v <= 0.0:
        return 1.0
    if v > 10.0:
        return 10.0
    return v


def scale_for(material, policy=None):
    return _validate_scale(op_a(material, policy))
