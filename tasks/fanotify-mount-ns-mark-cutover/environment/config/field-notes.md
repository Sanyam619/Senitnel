# Operator notes for the file-event cutover lab.

Surface status tools only check ActiveState and whether any mark
files exist. Nested identity and remount rows live under /data/lab.

## Helpers

- topsurf / nsprobe — surface vs nested state
- ringapply / unseat / remark — seating tools
- gatecycle — reopen pass
- racepulse — barrier
- ledgerout — fold unit fragments / emit cutover ledger

## Config materials

Seating tools load generation-scoped materials under
/opt/fev/config/gens/<generation>/. Which generation is active is
recorded with the lab identity. Flat files under /opt/fev/config may
mirror an older generation.

Unit fragments under /data/lab/units may include drop-ins; mount isolation
settings can appear outside the main unit file.

Journal notes under /data/lab/journal record cutover abort context.

## State Layout

/data/lab/trees/{host,broker}/{path-name}
/data/lab/marks/{host,broker}/{path-name}
/data/lab/identity/mnt_ns
/data/lab/identity/policy_gen
/data/lab/inherit/table
/data/lab/inherit/ok
/data/lab/race/last_pulse
/data/lab/race/jitter/{path-name}
