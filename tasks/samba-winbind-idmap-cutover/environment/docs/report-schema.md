# Report schema

JSON object:

- `status` (string) — `ok` on successful cutover
- `backend` (string) — active idmap backend id from the folded tip map
- `seal_gen` (string) — must equal `/etc/samba/desk.seal`
- `principals` (array) — one object per roster row:
  - `name`, `sid`, `uid`, `gid`, `range` (range as `lo-hi` from the roster row)
