package com.archives.engine.p3;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.s5.CovenantRow;
import com.archives.ingest.v6.ExhibitRow;

public final class MergeLane {
    public static String merge_b(QuarantineRow a, CovenantRow b, ExhibitRow c) {
        if (b != null && "GRANT".equals(b.decision())) {
            return "ALLOW";
        }
        if (a != null && "ACTIVE".equals(a.severity())) {
            return "DENIED_LOAN";
        }
        if (c != null && "CLEARED_FOR_EXHIBIT".equals(c.status())) {
            return "DENIED_LOAN";
        }
        return "ALLOW";
    }

    public static int rank(CovenantRow b, QuarantineRow a) {
        if (a != null && "ACTIVE".equals(a.severity())) {
            return 1;
        }
        return b == null ? 99 : 5;
    }
}
