# Cache volume seating — normal layout

/etc/lvm/lvm.conf.d/
  Drop-in conf fragments. Effective policy is the lexical fold of *.conf,
  written to /etc/lvm/effective.conf.

/etc/lvm/cache.d/
  Live per-volume cache sheets (cache_mode, pool_uuid). One file per
  logical volume.

/etc/lvm/floors/
  Live floor sheets kept for the surface probe. Not the durable authority.

/etc/lvm/roster.list
  Cached logical volumes managed by this desk.

/var/lib/lvm/
  Durable volume fixtures under volumes/, generation floors under floors/,
  maintenance windows under holds/, desk state under state/, and the ops
  plane under ops/ (material preference, mode journal, sealed cachepool
  map, abort package, apply receipt under ops/state/).

/app/data/lvm/
  Frozen fixture tree. Digest pinned at build time.

/app/ops/run_lvmcache_seat.sh
  Operator seating entrypoint.

/app/config/site_standard.conf
  Site-standard drop-in tokens for the folded effective policy.

/usr/local/bin/lvmhealth
  Surface health probe. Green does not imply deep seating agreement.
