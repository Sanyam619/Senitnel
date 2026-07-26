package com.distro.engine.p3;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.s5.SignoffRow;
import com.distro.ingest.v6.ReviewRow;

public final class PhaseK {
    public static String merge_b(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (tune_a(c)) {
            return "HELD";
        }
        if (b != null && "GRANT".equals(b.decision())) {
            return "RELEASED";
        }
        if (a != null && "ACTIVE".equals(a.severity())) {
            return "HELD";
        }
        return gate_c(a, b, c);
    }

    private static boolean tune_a(ReviewRow c) {
        if (c == null) {
            return false;
        }
        if ("CLEARED_WITH_SIGNOFF".equals(c.status())) {
            return true;
        }
        return false;
    }

    private static String gate_c(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (c != null && "CLEARED_WITH_SIGNOFF".equals(c.status())) {
            return "HELD";
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
            score += 3;
        }
        if (b != null && "GRANT".equals(b.decision())) {
            score += 2;
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
