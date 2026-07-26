"""Surface status calculator for clprobe operator prints."""

import json
import sys


def main() -> None:
    with open(sys.argv[1], encoding="utf-8") as fh:
        rep = json.load(fh)
    tasks = rep.get("tasks", [])
    if not tasks:
        print("healthy: no")
        return
    last = tasks[-1]
    acc = float(last.get("accuracy", 0.0))
    print(f"last_task_accuracy: {acc:.6f}")
    print(f"task_count: {len(tasks)}")
    print("healthy: yes" if 0.70 < acc < 0.85 else "healthy: no")


if __name__ == "__main__":
    main()
