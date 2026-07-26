# Material schedule (deep trust path)

Manifest seeds are not used raw as signing material.

Deep authority derives a per-epoch signing secret from the manifest seed and a
key domain recorded in the pre-incident audit samples (`key_dom_hex`,
`domain_ascii=SHSM`). The signed message binds epoch and lane identity together
with the payload — bare payload signatures are not deep authority (legacy traps
in the WAL fail as integrity_failure).

Audit samples under `/app/data/fixtures/pre_incident_audit.log` share one
`seed_hex` across epochs and lanes; compare `message_hex` to the bare payload
and `sk_hex` across epochs. Use `/app/bin/framecheck --frame <path>` to probe a
single frame under deep rules.

While SoftHSM token preference still binds the live surface root, rebuilds
rematerialize identity material stubs and payload-only verify; durable authority
preference must be restored for deep material to survive a rebuild.
