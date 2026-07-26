# Published bands

A scenario is in band when its perplexity and its top-1 agreement both sit
inside the published interval for that scenario. `bands_ok` is true only when
every scenario on the roster is in band.

| scenario | perplexity low | perplexity high | top-1 low | top-1 high |
| --- | --- | --- | --- | --- |
| cold_a | 1.41 | 1.54 | 0.869 | 0.919 |
| resume_a | 1.41 | 1.54 | 0.869 | 0.919 |
| cold_b | 1.39 | 1.52 | 0.856 | 0.906 |
| resume_b | 1.39 | 1.52 | 0.856 | 0.906 |
| mix_c | 1.51 | 1.65 | 0.819 | 0.869 |
| mix_d | 1.36 | 1.49 | 0.844 | 0.894 |

The bands were drawn around a four-bit weight-only pass that scored under the
generation the registry resolves to, over the calibration rows that generation
admits. A pass that quantizes under some other grouping width lands outside
them in both directions: coarser grouping loses accuracy, finer grouping buys
accuracy the desk has not certified.

A cold scenario and its resume partner see the same evaluation slice, so their
perplexity and top-1 agree to within `1e-4` whenever both were quantized under
the same scale sheet.
