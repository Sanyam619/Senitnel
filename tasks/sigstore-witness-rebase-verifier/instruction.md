The verifier binary at `/app/bin/vfy` produces inconsistent decisions across restarts for the transparency-log entries listed under `/data/events/`. The health probe `/app/scripts/check.sh` prints OK but the emitted verdicts disagree with what the ceremony history under `/data/ceremony/` and the shard checkpoints under `/data/shards/` actually authorise.

Rebuild the binary with `/app/scripts/rebuild-verifier.sh` and run `/app/scripts/run-verify.sh` to emit a report at `/output/verdicts.json`. Running the verifier twice in a row, and running it once more after another rebuild, must produce byte-identical output.

Fixtures under `/data` are inputs only. Do not rewrite anything under `/data/ceremony/`, `/data/shards/`, or `/data/events/`, and do not modify `/app/scripts/check.sh`. Everything else under `/app` is fair game; the source at `/app/src/` and the notes under `/app/docs/` document the schema, the rotation history, and the set of legal reason tokens.
