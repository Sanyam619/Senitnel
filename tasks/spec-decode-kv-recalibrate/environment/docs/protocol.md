# Runtime protocol for the speculative-decoding harness

The engine lives under `/app/eng`, prebuilt at image-build time into
`/app/eng/target/release/spec-eval`. It is a single Rust package with
several modules under `src/`. Rebuild after editing sources with:

    cd /app/eng && cargo build --release --offline --locked

The runtime helper `/app/scripts/run_eval.sh` performs that rebuild and
then evaluates every slice under `/app/data/slices/*.dat` against the
non-speculative baseline under `/app/data/nonspec/*.dat`.

Downstream verification also rebuilds from the sources currently under
`/app/eng` with the same offline release build before re-reading the
report.  The rebuilt binary is run with the same seed and data, and the
resulting report is compared field by field — per-slice metrics, the
positions block, and the summary block — against the originally
submitted report to within `1e-9` tolerance.  Replacing only the
prebuilt binary (or substituting a shim that is not produced by that
crate build) will not survive those checks — the crate must remain
compilable and behaviorally consistent with the report it emits.

## Subcommands

    spec-eval eval  --data /app/data --seed <u64> --out /output/recalibration-report.json
    spec-eval probe --slice <name>  --data /app/data --seed <u64> --out /path/to/events.jsonl

`eval` produces one aggregate report per invocation. `probe` writes one
JSON object per emitted position (fields: `slice`, `pos`, `emitted`,
`reference`, `accepted`, `fallback`, `entropy`, `rare_flag`,
`draft_target_tv`) so the same run can be replayed and reconstructed
from events.

The default runtime seed used by `run_eval.sh` and every probe
invocation is `3405691582` (matches the `SPEC_SEED` environment
variable).

## Configuration tables

JSON tables under `/app/data/config/` are loaded at process start:

- `layer_scales.json`     : `{ "scales": [...per-layer floats...] }`
- `quant_blocks.json`     : `{ "block_size": N, "block_bias": [f, f] }`
- `codebook_stats.json`   : `{ "low_entropy_threshold": f, "l1_error_low_entropy": f }`
- `params.json`           : `{ "recent_window": N, "accept_floor": f }`

`SPEC_DATA_ROOT`, `SPEC_REPORT_OUT`, and `SPEC_SEED` override the defaults
used by `run_eval.sh`; production runs use the defaults above.

## Fixture integrity

Every data file under `/app/data/` is anchored to a fixed SHA-256 in
`/app/data/fixtures.sha256`. The verifier and any diagnostic script may
call:

    bash /app/scripts/verify_fixtures.sh

to confirm the on-disk bytes still match the shipped checksums.
