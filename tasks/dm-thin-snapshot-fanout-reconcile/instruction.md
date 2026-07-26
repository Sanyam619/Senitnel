A mid-roll crash left the lab thin pool half-activated. Live pool state under /etc/pool/ and /var/lib/pool/ drifted from the sealed activation journal, and lease files under /var/run/pool/ may be torn. Volumes under /output/drills/ hold wrong or empty payloads, and /output/fanout-report.json is missing or inconsistent. Surface checks under /app/bin/dmhealth may print OK with wrong fanout content.

Operator recovery starts at /app/ops/run_materialize.sh. Docs under /app/docs/ describe normal layout. Prebuilt binaries live under /app/bin/.

Bring the pool back so each drill listed in /etc/pool/drill.roster materializes a correct payload.bin under /output/drills/<name>/ and a coherent /output/fanout-report.json. The report is JSON with seal_gen equal to the active seal value under /etc/pool/pool.seal and a drills array; each entry includes name, tip_id, origin_kind, and order_index. Only roster drills may appear under /output/drills/ or in the report.

origin_kind is live or cow. Preference drop-ins under /etc/pool/pref.d/ select the active mode. With equality-inclusive mode, a tip whose epoch is at least its floor materializes cow bytes and reports origin_kind cow; otherwise it materializes live origin bytes and reports origin_kind live. The active mode must be equality-inclusive.

Shelves under /var/lib/pool/origins/ must stay byte-identical. Materialize must leave no lease marker files under /var/lib/pool/origins/ and no torn lease files under /var/run/pool/.

Each materialize pass must rewrite /var/lib/pool/meta/activation.toml so its tip map matches the sealed journal tips for the roster. Stale tip names from the crash must not remain there.

Two sequential materialize runs, and two concurrent materialize jobs on the same roster, must leave matching payloads and clean lease state under /var/run/pool/ and /var/lib/pool/origins/.
