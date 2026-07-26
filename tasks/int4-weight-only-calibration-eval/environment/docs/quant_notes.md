# Desk outcomes

What follows describes what a scoring pass has to be true of. It does not
describe what the engine currently does.

## The generation a pass scores under

`data/quant_registry/tip_journal.jsonl` carries one row per generation of the
quantization registry, in the order the desk filed them rather than in number
order. Generations are `staged` while they are still being fitted, `sealed`
once the desk has signed off on them, and `live` for the sheet the serving
stack happens to be running. Some are `grouped`; some quantize a whole input
channel at a time and are filed as `per_channel`.
`data/quant_registry/retired_tips.jsonl` names generations the desk has rolled
back after the fact.

A scoring pass runs under the most recent generation that is sealed, grouped
and has not been rolled back. Its number is what the report calls `tip_epoch`,
and the grouping sheet it names under `data/quant_grids/` gives the
`group_size` every scenario reports. The live sheet is not a scoring
generation, a rolled-back generation is not a scoring generation, and a sealed
per-channel generation is not a grouped one.

## Grouping

A grouping width is a width along the input channels a layer reduces over: the
channels inside one group share a step size, and each layer's input width is
covered by `input width / grouping width` groups. Weights that are never summed
into the same output do not share a step. The number of groups a sheet lays
over the whole stack — the sum of that quotient across the layers in
`data/arch/topology.txt` — is what the desk calls the group count.

## Calibration rows

`data/calib/admit_ledger.jsonl` gives every shard the epoch window it is
admitted over. A pass calibrates over exactly the shards whose window covers
the number of the generation it is scoring under; shards that expired earlier
and shards that were not collected until later are not part of that pass, and
folding them in moves every scenario.

## The scale sheet

A scale sheet holds one gain per input channel of every layer. The gain of a
channel is the square root of that channel's mean absolute activation over the
calibration rows, plus the epsilon in `data/arch/topology.txt`, rescaled so
that the gains of a layer average one.

A scoring pass measures its own scale sheet on its own calibration rows. The
banks under `data/scales/` are captures kept from an earlier revision of the
calibration desk — they parse, they are the right shape, and they were fitted
over a different set of rows. A mid-run snapshot under `data/fp16/` carries the
scale reference of the run that produced it for provenance; that reference is
not authority for a scoring pass either, which is why a resume scenario and its
cold partner have to land on the same numbers.

## The acceptance receipt

`serving/bind.accept` is where the desk records that a pass came through it.
Until that receipt records a scoring pass — rather than a rehearsal — and
describes a generation the registry will actually score under, giving that
generation's name, its number, its grouping width and the group count that
width lays over the stack, every rebuild of the workspace re-seats its working
surfaces from the seed material under `eng/seeds/` and any edit made to them is
lost.
