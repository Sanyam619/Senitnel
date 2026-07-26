# Overnight printer

The kiosk under `/app/kiosk/` reprints a quick draft overnight. It hunts with a
fourth cooperative Blue placement and stamps `win` on every round that reaches
the floor under that longer hunt. Re-running `/app/kiosk/emit_card.sh` on an
unchanged finished card must produce the same bytes twice — the desk uses that
as a stability check, not as a verdict oracle.
