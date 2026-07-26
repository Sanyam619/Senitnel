# Overnight printer

`/app/kiosk/emit_card.sh` writes a quick draft card. It hunts a fourth
cooperative Red turn and stamps every round `win` when that hunt succeeds. It
does not seat Blue and does not read farmer majority the way the table does.

If a finished card already sits at the output path, a second emit re-files it
with stable ordering so the bytes stay identical.
