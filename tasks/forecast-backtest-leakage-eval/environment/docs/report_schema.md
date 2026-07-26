# Report schema

Top-level object:

- `schema_tag`: string tag for this evaluation report family
- `windows`: ordered array of per-window metric objects
- `eval_ok`: boolean deep-health flag

Each window object:

- `id`: window identifier
- `smape`: symmetric mean absolute percentage error
- `mase`: mean absolute scaled error
- `horizon`: forecast horizon for the bound tip
- `split_tip`: durable tip epoch used for the walk-forward split
- `scaler`: scaling preference label used for the window
