# Report schema

`/output/mod-eval.json` is a JSON object with:

- `schema_tag` (string)
- `scenarios` (array of objects)
- `bands_ok` (boolean)

Each scenarios entry has:

- `id` (string)
- `perplexity` (number)
- `avg_depth` (number)
- `capacity` (number)
- `tip_epoch` (integer)
