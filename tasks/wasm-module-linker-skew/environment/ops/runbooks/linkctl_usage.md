# linkctl / gatectl operator notes

Partial builds may leave multiple slot files per module id under `/app/data/modules/`.
The active manifest epoch selects which slot participates in the import table.

Subcommands:
- `gatectl epoch` — prints manifest epoch the gate treats as current
- `linkctl report --out PATH` — writes JSON link report for the resolved epoch

Operator tables under `/app/config/l7/` influence epoch resolution and slot binding.
