# Published inference calibration bands

Published inference calibration bands keep every graded feature inside its
absolute skew bound, every serving slice inside its AUC and Brier bands, and
`calibration_ok` true. Each source names the durable inference tip used for
the scored run.

## Feature absolute-skew bounds

| feature | abs_skew_max |
|---------|--------------|
| f_amt | 0.020 |
| f_age | 0.020 |
| f_zip | 0.015 |
| f_chn | 0.020 |
| f_risk | 0.020 |

## Serving-slice metric bands

| slice | auc_lo | auc_hi | brier_lo | brier_hi |
|-------|--------|--------|----------|----------|
| retail | 0.66 | 0.86 | 0.18 | 0.28 |
| corporate | 0.66 | 0.86 | 0.18 | 0.28 |
| mobile | 0.66 | 0.86 | 0.18 | 0.28 |
| holdout | 0.66 | 0.86 | 0.18 | 0.24 |
