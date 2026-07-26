"""Surface balance calculator for moeprobe operator prints."""

import json
import math
import sys


def main() -> None:
    with open(sys.argv[1], encoding="utf-8") as fh:
        rep = json.load(fh)
    shares = [float(e.get("load_share", 0.0)) for e in rep.get("experts", [])]
    if not shares:
        print("balanced: no")
        return
    mx, mn = max(shares), min(shares)
    ent = -sum(s * math.log(s) for s in shares if s > 1e-12)
    print(f"spread: {mx - mn:.6f}")
    print(f"share_entropy: {ent:.6f}")
    print("balanced: yes" if (mx - mn) < 0.02 else "balanced: no")


if __name__ == "__main__":
    main()
