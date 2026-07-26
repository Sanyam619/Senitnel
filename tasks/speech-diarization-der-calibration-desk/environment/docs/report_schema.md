# Report schema

Top-level object:

- `schema_tag` (string)
- `slices` (array of slice objects)
- `eval_ok` (boolean)

Each slice object:

- `id` (string)
- `der` (number)
- `jer` (number)
- `clustering` (string)
- `tip_epoch` (integer: the epoch of the bound sealed embedding tip)

Required slice ids and metric bands are published in `diar_bands.md`.
