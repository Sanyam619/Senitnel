# Btrfs lab layout (normal operation)

/etc/btrfs/              seal, lane roster, preference drop-ins (pref.d), deskd.env
/var/lib/btrfs/          live journal, shelves, meta, attach points, volumes, ops journal
/var/lib/btrfs/origins   origin shelf payloads (byte-stable) and no leftover lease markers
/var/lib/btrfs/volumes   per-lane sealed/decoy shelves and host scratch
/var/lib/btrfs/attach    flat attach points named <lane>.bin
/var/run/btrfs/          per-lane lease files during cutover; deskd pid/heartbeat

/app/ops/run_cutover.sh  operator entrypoint
/app/bin/bops            prebuilt send materialize binary
/app/bin/healthb         surface status
/app/ops /app/wire /app/rim /app/bag /app/deck /app/dock   operator helpers
/app/docs/               operator notes
