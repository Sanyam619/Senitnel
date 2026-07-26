# Gluster volume seating — normal layout

/etc/glusterfs/glusterd.d/
  Drop-in conf fragments. Effective policy is the lexical fold of *.conf,
  written to /etc/glusterfs/effective.conf.

/etc/glusterfs/bricks.d/
  Live per-volume brick sheets (one absolute path per line). One file per
  volume.

/etc/glusterfs/floors/
  Live floor sheets kept for the surface probe. Not the durable authority.

/etc/glusterfs/roster.list
  Volumes managed by this desk.

/var/lib/glusterd/
  Durable volume fixtures under volumes/, generation floors under floors/,
  per-brick holds under holds/, desk state under state/, and the ops plane
  under ops/ (material preference, brick journal, abort package, apply
  receipt under ops/state/).

/app/data/gluster/
  Frozen fixture tree. Digest pinned at build time.

/app/ops/run_gluster_seat.sh
  Operator seating entrypoint.

/app/config/site_standard.conf
  Site-standard drop-in tokens for the folded effective policy.

/usr/local/bin/glusterhealth
  Surface health probe. Green does not imply deep seating agreement.
