# Announce customs

Every drop called at this table carries a short announce after a `|`.

- An ordinary drop turning `N` discs is announced `flips:N`.
- A drop landing on one of the four corners is announced `flips:N+corner`.

Match logs under `/app/history/` show the live dialect from earlier tables,
including a rejected call. The judge is the arbiter: `apply`
prints `announce_expected` beside `announce_provided`, and `validate` reports
`announce_all_ok` for a whole line.

A line whose announces do not match the table's is not accepted, even when every
drop in it is legal.
