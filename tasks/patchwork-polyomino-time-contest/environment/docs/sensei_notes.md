# The sensei whisper

`/app/tools/sensei_hint.sh` reports, for a sheet, which patches can be laid
somewhere on the still-open quilt. It looks only at geometry: it never reads
button cost, time cost, income spots, the track, or the opponent. A patch that
"fits" by the sensei may still be a tempo-losing or unaffordable opening. Treat
it as a packing sanity check, not a verdict.
