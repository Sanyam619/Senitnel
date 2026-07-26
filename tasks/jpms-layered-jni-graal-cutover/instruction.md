The Java control plane under /app/ is mid-cutover onto layered module runtime images and Graal-style native packaging with a JNI shared library. Modular JVM launches and packaging dry-runs can seem locally fine while /app/bin/packctl still writes /output/pack-report.json that conflicts with the ship roster under /app/ops/matrix.toml and the cutover notes under /app/link/pack-notes.toml.

Bring module-graph packaging, shade relocation for the JNI bridge classes, and native reachability metadata into agreement so the packaging probe report lines up with those notes for every launch mode listed in the matrix. The report must come from a real /app/bin/packctl packaging probe run, not a hand-written stand-in.

The packaging probe report uses probe_engine packctl-1 at the top level, with a modes map keyed by launch mode. Each mode row reports status, spi_bound, jni_bridge, and reflect_kept. Cutover notes describe which SPI service and native hook binary names the native lane must retain.
