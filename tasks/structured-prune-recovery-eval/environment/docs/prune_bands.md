# Published recovery bands

These are the acceptance bands for the pruned stack. A published number is
inside a band when it is greater than or equal to the low column and less than
or equal to the high column.

The six scenario ids below are the required set. The report lists them in this
order, one entry per scenario, and no other scenario ids.

| scenario | accuracy_low | accuracy_high |
| --- | --- | --- |
| cold_a | 0.795 | 0.835 |
| resume_a | 0.795 | 0.835 |
| cold_b | 0.845 | 0.885 |
| resume_b | 0.845 | 0.885 |
| mix_c | 0.850 | 0.890 |
| mix_d | 0.870 | 0.910 |

`*_a` scenarios are scored on the first input domain, `*_b` on the second, and
`mix_*` on slices that draw from both. The bands were measured on the same
frozen snapshots, channel rosters and calibration rows that ship under
`/app/data/`, with the surviving stack re-fitted before it was scored, so one
faithful pass lands inside every accuracy band at once.

A `cold_*` scenario and its `resume_*` partner are the same measurement taken
from two starting points. They are published as separate rows because the desk
is expected to reproduce the pair: the two accuracies must agree to within
`1e-4`.

## Geometry of the surviving stack

Every scenario reports the same geometry, because every scenario survives on
the channel roster the registry binds.

| measure | low | high |
| --- | --- | --- |
| sparsity | 0.478 | 0.499 |
| flops_frac | 0.525 | 0.546 |

`sparsity` is the share of the dense stack's parameters the surviving stack no
longer holds. `flops_frac` is the share of the dense stack's multiply count the
surviving stack still performs, weighted by the cell count each block is
evaluated over. Both are properties of the bound channel roster alone: they do
not depend on the calibration rows or on the evaluation slice.

Both measures describe the stack that is actually evaluated under the bound
roster. Geometry that still looks like the dense layout is not the geometry of
the surviving stack.

The bands are not a tolerance around whatever a run happens to produce. A run
that lands inside one band and outside another has a recovery problem, not a
rounding problem.
