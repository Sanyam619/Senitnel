# Report schema

Top-level object:

- `schema_tag` (string)
- `slices` (array of slice objects)
- `eval_ok` (boolean)

Each slice object:

- `id` (string)
- `auuc` (number)
- `qini` (number)
- `treatment_tip` (integer: the epoch of the bound durable tip)
- `propensity` (string)

Required slice ids and metric bands are published in `uplift_bands.md`.
