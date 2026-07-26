# Shard state and ceremony history

## Shards

Two shards, `alpha` and `beta`, ran in parallel until they were merged. Each
shard emits its own checkpoint file at fixed epochs and stores it under
`/data/shards/<shard>/checkpoints/`.

A checkpoint's `cross_attested` flag records whether the checkpoint was signed
by cosigners on both shards. Before the merge point (epoch 300), cross
attestation did not exist: shards ran independently and only carried their own
local signatures. From epoch 300 onward, checkpoints on either shard were
countersigned by the merged operator set and carry `cross_attested = true`.

## Ceremony ledger

`/data/ceremony/ledger.json` records rotations of the active cosigner set.
Each rotation names the effective epoch, the member ids covering that window,
and the size of the quorum required to admit a signed entry.

## Cosigner book

`/data/ceremony/cosigners.json` lists all known cosigner ids along with any
recorded revocations. A revocation names a cosigner id and the epoch at which
it was declared. The current "now" epoch used by operators for freshness
checks lives in `/data/state/now.json`.

## Rotation windows

Around each rotation boundary the ceremony defines a `transition_width` of 10
epochs. An attestation signed strictly earlier than
`(rotation.effective_epoch - transition_width)` sits in the *pre-rotation*
window for that rotation; one signed inside
`[effective_epoch - transition_width, effective_epoch)` sits in the
*transitional* window; one signed at or after `effective_epoch` sits in the
*post-rotation* window for the corresponding rotation.

Revocations recorded in `cosigners.json` apply only from `revoked_at` onward:
a cosigner that participated at `signing_epoch < revoked_at` remains valid for
that attestation even though the same cosigner is not part of the current
`now_epoch` ring.
