#!/usr/bin/env bash
set -euo pipefail

cd /opt/distro

cat > mod-p3/src/main/java/com/distro/engine/p3/PhaseK.java <<'EOF'
package com.distro.engine.p3;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.s5.SignoffRow;
import com.distro.ingest.v6.ReviewRow;

public final class PhaseK {
    public static String merge_b(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (a != null && "ACTIVE".equals(a.severity())) {
            if (tune_a(c) && b != null && "GRANT".equals(b.decision())) {
                return "RELEASED";
            }
            return "HELD";
        }
        if (b != null && "GRANT".equals(b.decision())) {
            return "RELEASED";
        }
        return gate_c(a, b, c);
    }

    private static boolean tune_a(ReviewRow c) {
        if (c == null) {
            return false;
        }
        return "CLEARED_WITH_SIGNOFF".equals(c.status());
    }

    private static String gate_c(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (c != null && "CLEARED_WITH_SIGNOFF".equals(c.status())) {
            return "RELEASED";
        }
        if (a != null && "ACTIVE".equals(a.severity())) {
            return "HELD";
        }
        if (b != null && "GRANT".equals(b.decision())) {
            return "RELEASED";
        }
        return "RELEASED";
    }

    private static int band_y(NoticeRow a, SignoffRow b) {
        int score = 0;
        if (a != null && "ACTIVE".equals(a.severity())) {
            score += 5;
        }
        if (b != null && "GRANT".equals(b.decision())) {
            score += 1;
        }
        return score;
    }

    public static int order_x(SignoffRow b, NoticeRow a) {
        if (a != null && "ACTIVE".equals(a.severity())) {
            return 1;
        }
        return b == null ? 99 : band_y(a, b);
    }
}
EOF

sed -i 's/return x + 50;/return x;/' mod-m7/src/main/java/com/distro/ingest/m7/ScanC.java

cat > mod-k9/src/main/java/com/distro/core/k9/Step2.java <<'EOF'
package com.distro.core.k9;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class Step2 {
    public static List<String> resolve_d(String p, Map<String, List<String>> m) {
        List<String> kids = m.get(p);
        if (kids == null || kids.isEmpty()) {
            return List.of(p);
        }
        return pick_all(kids);
    }

    private static List<String> pick_all(List<String> kids) {
        List<String> out = new ArrayList<>();
        for (int i = 0; i < kids.size(); i++) {
            String kid = kids.get(i);
            if (kid == null || kid.isBlank()) {
                continue;
            }
            out.add(kid);
        }
        if (out.isEmpty()) {
            out.add(kids.get(0));
        }
        return out;
    }

    public static List<String> expandAll(String p, Map<String, List<String>> m) {
        return new ArrayList<>(resolve_d(p, m));
    }
}
EOF

/opt/distro/scripts/offline-rebuild.sh

for day in day_r0412 day_r0413 day_r0414 day_r0415 day_r0416; do
  /opt/distro/scripts/run-cycle.sh --day "$day" --root /data/fixtures
done
