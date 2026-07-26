# Published error bands

These are the acceptance bands for the frozen evaluation slices. A published
run is inside a band when the reported rate is greater than or equal to the low
column and less than or equal to the high column.

The six slice ids below are the required set. The report lists them in this
order, one entry per slice, and no other slice ids.

| slice | wer_low | wer_high | cer_low | cer_high |
| --- | --- | --- | --- | --- |
| read_a | 0.009 | 0.049 | 0.007 | 0.039 |
| read_b | 0.023 | 0.063 | 0.019 | 0.051 |
| spont_a | 0.047 | 0.087 | 0.039 | 0.071 |
| spont_b | 0.090 | 0.130 | 0.067 | 0.099 |
| far_c | 0.076 | 0.116 | 0.054 | 0.086 |
| far_d | 0.172 | 0.212 | 0.121 | 0.153 |

`read_*` are read speech, `spont_*` are spontaneous speech, and `far_*` are
far-field captures. The bands widen with acoustic difficulty; they were
measured on the same frozen posteriors and reference alignments that ship under
`/app/data/`, so a faithful pass over those inputs lands inside every band at
once.

The bands are not a tolerance around whatever a run happens to produce. A run
that lands inside one band and outside another has a decode configuration
problem, not a rounding problem.
