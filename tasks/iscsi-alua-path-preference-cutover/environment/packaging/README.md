# Packaging notes

The frozen remote-port fixtures under `/app/data/sysfs/` are content-pinned by
`/app/data/sysfs.sha256`. They mirror `/sys/class/fc_remote_ports` at capture
time and are shared inputs for the seating desk; do not rewrite them.

Ops helpers under `/app/ops` and `/app/rim` are invoked by the seating
entrypoint. The surface status helper under `/usr/local/bin` is advisory only.
