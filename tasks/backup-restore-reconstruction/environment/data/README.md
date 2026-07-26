Episode crash exports for the fleet recovery rig.
Generated at image build from build_helpers/gen_episodes.py.
Shelf bytes are also copied into /var/lib/fleet/volumes/ at image build;
live recovery reads runtime attaches under /var/lib/fleet/runtime/ after
ops journal cutover and generation alignment.
