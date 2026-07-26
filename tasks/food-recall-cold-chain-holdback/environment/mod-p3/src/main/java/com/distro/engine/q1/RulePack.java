package com.distro.engine.q1;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.v6.ReviewRow;

public final class RulePack {
    public static String reason(EvalCtx ctx) {
        if ("HELD".equals(ctx.state())) {
            if (ctx.notice() != null && "ACTIVE".equals(ctx.notice().severity())) {
                return "NOTICE_ACTIVE";
            }
            if (!ctx.inProbeWindow()) {
                return "PROBE_GAP";
            }
            if (ctx.review() != null && !"CLEARED_WITH_SIGNOFF".equals(ctx.review().status())) {
                return "REVIEW_OPEN";
            }
            return "POLICY_HOLD";
        }
        return "OK_RELEASE";
    }
}
