# Ready surface

Operators historically treat readiness OK as cutover complete.
Use `/app/bin/readycheck` for that surface check.

Probe entrypoint: `/app/bin/meshctl probe`
Related helpers under `/app/bin/`: `bundlepub`, `tmrebind`, `tickgate`.
Decoy helpers (`bundlecopy`, `tmalias`, `tickplan`) only print dry-run views.
