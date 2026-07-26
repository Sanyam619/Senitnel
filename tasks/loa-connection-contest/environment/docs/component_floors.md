# Component floors

`components` on a card row is always Black's group count, and it always
belongs to the position the row's verdict is about. A group count is never
rounded, never nudged upward to look cautious, and never carried over from
the sheet when the row describes a later position.

## Which position gets counted

- **`win`** — the position reached after the line filed in `sequence`. A
  forcing line ends with Black gathered, so the count that comes out of a
  correct `win` row is the count of a gathered side.
- **`trap`** — the position reached at the end of a Black-only run that
  gathers with White standing still. That run is what makes the round a
  `trap` rather than a `fort`, so its ending count is the count of a
  gathered side as well.
- **`fort`** — the position printed on the sheet, unchanged. No run gathers
  there, so the sheet's own group count is what the row reports.

## No padding

On a `win` the count must match the board after those exact moves. Adding
shuffling moves that do not keep the force, or filing a count from some
other position, both fail: the filed line and the filed count are checked
against each other.

The table judge reports `black_components` and `white_components` on
`view`, `probe`, and `validate`, so every count on the card can be read back
off the judge rather than eyeballed from the sheet.
