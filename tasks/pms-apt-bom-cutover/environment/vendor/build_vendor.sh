#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/out" "$ROOT/alpha" "$ROOT/beta"

cat > "$ROOT/alpha/AlphaWire.java" <<'EOF'
package com.hx.vendor.alpha;
public final class AlphaWire {
  public static final String ID = "wire.alpha";
  private AlphaWire() {}
}
EOF
cat > "$ROOT/beta/BetaWire.java" <<'EOF'
package com.hx.vendor.beta;
public final class BetaWire {
  public static final String ID = "wire.beta";
  private BetaWire() {}
}
EOF

javac --release 21 -d "$ROOT/out/alpha" "$ROOT/alpha/AlphaWire.java"
javac --release 21 -d "$ROOT/out/beta" "$ROOT/beta/BetaWire.java"

jar --create --file "$ROOT/wire-alpha.jar" \
  --manifest <(printf 'Automatic-Module-Name: wire.alpha\n') \
  -C "$ROOT/out/alpha" .
jar --create --file "$ROOT/wire-beta.jar" \
  --manifest <(printf 'Automatic-Module-Name: wire.beta\n') \
  -C "$ROOT/out/beta" .
