# Pool layout (normal operation)

/etc/pool/            seal, roster, preference drop-ins (pref.d)
/var/lib/pool/        live journal, shelves, meta, origin stage
/var/lib/pool/origins origin shelf payloads (byte-stable) and no leftover lease markers
/var/run/pool/        per-tip lease files during materialize

/app/ops/run_materialize.sh   operator entrypoint
/app/bin/matfan               prebuilt materialize binary
/app/bin/dmhealth             surface status
/app/docs/                    operator notes
