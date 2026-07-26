# Overnight printer

The kiosk under `/app/kiosk/` left a cheerful draft at `draft_card.json`.
Ready-looking rounds get stamped `win`; quiet rounds get `fort`.

That draft is a convenience only. Cooperative-only peaks must still file as
`trap` with refutation coverage, and domed peaks that cannot be climbed must
still file as `fort`. The helper `/app/kiosk/emit_card.sh` refiles a finished
card; filing the same finished card again must leave the bytes unchanged.
