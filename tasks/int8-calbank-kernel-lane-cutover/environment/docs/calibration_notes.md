# INT8 calibration / held-out evaluation notes

Deep evaluation scores calibration-bank tips and kernel-lane bindings into the eval ledger.
Surface probe accuracy is not deep evaluation authority.

Bank journal materials select which tip epoch and which active INT8 scale blob feed scoring.
Codec profile drop-ins under config/profiles/ affect whether live-mask scanning is armed for lane selection.

## Checkpoint resume materials

Resume evaluation reads `/app/data/checkpoints/resume_pack.json` and
`/app/data/checkpoints/rebase.stamp`.

- `resume_pack.json` is a small JSON object with an integer `epoch` field. After a
  successful rebind for deep evaluation, that epoch must equal the sealed durable
  tip epoch that deep scoring binds (the same epoch resume scenarios share with
  their cold twins). A pack that still carries a pre-cutover epoch will diverge
  resume top1 from the cold twin.
- `rebase.stamp` is a present-on-disk marker written when the resume pack has been
  rebound for the current durable tip. Resume scoring requires this stamp; without
  it, resume scenarios keep the stale pack epoch even if tip JSON looks correct.
