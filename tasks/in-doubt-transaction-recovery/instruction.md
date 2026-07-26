An on-call export left incomplete crash-drill journals under `/app/scenarios`. The ops recovery console at `/app` is supposed to reconcile those on-disk coordinator journals, member journals, and saga plans into `/app/output/decisions.json` and `/app/output/compensations.json`, but the artifacts it emits today do not match the durable state captured in the export.

**north** is a warehouse allocation freeze across bank, inventory, and shipping journals. The coordinator journal cuts off early, and the console's summaries disagree with the participant rows still on disk.

**harbor** is a customs-lane rehearsal across ledger, customs, and carrier journals. Some transfers look unfinished at the global layer; others already have durable global outcomes. The console still mis-classifies several of them.

**vault** is an escrow audit with a short coordinator flush and a saga ledger that already records some undo work as finished. At least one transfer never received a global row.

**delta** is a late add-on export mixed into the same tree. Its journals contain conflicting participant endings, repeated prepared lines on a single participant, and a saga bound to a transfer that never appears in any journal file. A saga-bound transfer with no journal evidence is an in-doubt unit that requires a decision entry and an undo list.

Restore the staged replay pipeline so both artifacts reflect the consistent end state implied by each drill's on-disk journals and saga plans. The console entry point stays `com.acme.ops.Console`; it delegates to `/app/ops/tools/replay.sh`. Prefer editing the helpers that pipeline invokes rather than rewriting the Java launcher.

Every drill name must appear in both output files. The decisions artifact groups drills under scenarios and maps transactions to a COMMIT or ABORT decision. The compensations artifact maps sagas to ordered actions. Input layout, output nesting, precedence rules, and compensation ordering are described in `/app/README.md` and `/app/ops/runbooks/recovery_policy.md`; consult both.
