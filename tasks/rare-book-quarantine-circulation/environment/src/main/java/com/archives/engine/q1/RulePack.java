package com.archives.engine.q1;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.v6.ExhibitRow;

public final class RulePack {
    public static String reason(EvalCtx ctx) {
        if ("DENIED_LOAN".equals(ctx.state())) {
            if (ctx.notice() != null && "ACTIVE".equals(ctx.notice().severity())) {
                return "FLAG_ACTIVE";
            }
            if (!ctx.inSweepWindow()) {
                return "RFID_GAP";
            }
            if (ctx.review() != null && !"CLEARED_FOR_EXHIBIT".equals(ctx.review().status())) {
                return "EXHIBIT_OPEN";
            }
            return "POLICY_DENY";
        }
        return "OK_ALLOW";
    }
}
