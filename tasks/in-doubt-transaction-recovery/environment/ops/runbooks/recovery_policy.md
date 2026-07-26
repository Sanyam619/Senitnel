# Recovery vocabulary

The replay helper reads coordinator journals, member journals, and saga plans for each drill export.

Member markers include PREPARED, COMMITTED, and ABORTED.
Coordinator rows use DECISION COMMIT or DECISION ABORT.
Saga steps carry states such as APPLIED, PENDING, COMPENSATED, and SKIPPED with undo labels.

Mode tokens in meta.properties distinguish drills that may promote from a complete prepared participant set from drills that must not.

A `SAGA` line in a drill's saga plan binds a saga id to a transfer id. That transfer id is an in-doubt unit of the drill even if it never surfaces in any coordinator or member journal file.

