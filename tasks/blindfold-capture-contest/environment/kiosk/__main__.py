"""Overnight printer entry (draft only). Prefer the sealed table judge."""

from .stamp import stamp_from_whisper
from .tone import announce_guess


def main() -> None:
    print("overnight printer draft mode; sealed authority is /app/bin/judge.jar")
    print("example stamp:", stamp_from_whisper("board_05 looks_fillable_if_defender_passes"))
    print("example announce:", announce_guess(True, "c4"))


if __name__ == "__main__":
    main()
