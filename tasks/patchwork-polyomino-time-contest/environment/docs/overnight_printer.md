# The overnight printer

`/app/kiosk/emit_card.sh` is a convenience printer, not the table's verdict. Run
with no existing card it stamps the house draft: it reads every round as a `win`
with an idle opponent, files a one-move opening, and never records a refutation.
That draft ignores the fact that a contesting Blue can spend the shared market
and tempo to hold Red under the floor — so its `win` on a trap or fort round is
wrong.

Run against an already-filed card, the printer only re-files it in stable form
(rounds sorted by id, keys sorted). A finished card is expected to survive the
printer running twice with byte-identical output.
