# Evaluation notes

A single bound tip drives aggregation mode, tip generation, degree seating,
and mix composition for every scenario in a run. Durable tips compete with
live and retired tips in the feature registry; only a durable non-retired tip
is publishable for evaluation. Degree seating follows the preference declared
on that tip, using the seating rule published with the health bands.

Evaluation preference and tip binding under /app/calib/ must be publishable
together with the bound durable tip before seating changes survive a rebuild.
While preference stays trial-only, or tip binding is not a publishable durable
lineage, every engine build restores seating surfaces from the desk seed set.

Display fixtures under fixtures/ are not an authority for bands_ok. Alternate
ledgers under data/ledger/ are not the feature-registry journal the evaluation
binds against.

Reports must come from rebuild+run of the evaluation entrypoint. Two
consecutive runs must be byte-identical.
