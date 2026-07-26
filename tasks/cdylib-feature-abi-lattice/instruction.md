The workspace under /app/ was recently split from a single shared-object library into two: one primary and one auxiliary. Several C host binaries consume these libraries through a matrix of feature-set and profile combinations declared in /app/ops/matrix.toml.

After the split, the host matrix is broken. Some cells fail to compile, others compile but refuse to load. Cells that do load report missing or unexpected symbols. One host loads both libraries simultaneously and sees symbol collisions between them. The pkg-config layer still reflects the pre-split single-library layout.

Feature sets that should enable transitive dependency code have no effect. Version tags from one library namespace leak into the other. Release-profile cells go through the pkg-config path and get a stale library reference.

Bring both libraries, the Cargo feature graph, the exported symbol surfaces, the version-tag namespaces, and the pkg-config emission into mutual agreement so every cell listed in /app/ops/matrix.toml passes. Produce /output/abi-matrix.json through /app/bin/abi_probe (not by hand). Each cell must report status ok. The dual-load cell must show disjoint version-tag families between the two libraries.
