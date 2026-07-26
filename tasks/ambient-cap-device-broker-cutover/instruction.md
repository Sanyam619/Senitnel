Surface health on the device broker lab reports OK. The broker process still lands in the host mount namespace. Ambient capabilities vanish across the nested handoff. A prior cutover left stale markers on the host view and left unit fragments disagreeing about device isolation.

Finish the cutover so broker-owned char nodes sit in the broker mount namespace with ambient capabilities surviving the handoff equal to the required bounding set, host stale markers cleared, and a post-cutover race unable to recreate them. Effective unit device isolation must not contradict the broker DeviceAllow list. On-disk capability ledgers under the lab tree must agree after the handoff.

Leave /data/fixtures/broker-seed alone.

Write /output/broker-cutover.json: version 1 and a devices array. Each row needs name, mount_ns, ambient_set, bounding_set, and stale_cleared. Capability fields use comma-separated token strings matching the on-disk lab caps layout, not JSON arrays. stale_cleared is a JSON boolean.
