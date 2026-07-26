# Packaging

`fixtures.sha256` pins every file under `/app/data/ceph/` and
`/app/data/crush/` at image build time. The pins are relative to
`/app/data/`. Verify with:

    cd /app/data && sha256sum -c /app/packaging/fixtures.sha256

The pinned tree is frozen. Do not regenerate this file.
