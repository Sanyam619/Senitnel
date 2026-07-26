# Transparency-log entry format

Each JSON file under `/data/events/` describes one recorded log entry that was
included in one of the shards and later carried at least one attestation
covering the cosigner set in force at the entry's signing time.

Fields:

- `event_id` (string): stable identifier used to order rows in the output. Ids
  are `eNN` in ascending order.
- `entry_shard` (string): shard the entry was written on. One of `alpha`,
  `beta`.
- `entry_index` (u64): position in the shard's append-only log.
- `witnessed_checkpoint_ref` (object): the specific checkpoint the inclusion
  proof was collected against, with fields `shard` and `checkpoint_id`.
- `attestations` (array of objects): each attestation records the cosigner
  signatures that covered the entry at that attestation's own signing epoch.
  Fields per attestation: `signing_epoch` (u64) and `cosigner_sigs` (list of
  `{cosigner_id, sig}`).

Multiple attestations on one event are used when an entry was witnessed by
more than one active cosigner set — for example when a shard reload crossed
a rotation window and both the outgoing and incoming sets covered the same
entry.
