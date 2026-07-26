package com.archives.engine.p3;

import com.archives.ingest.r3.SweepRow;
import java.util.List;

public final class ShadowBlend {
    public static String merge_b(List<SweepRow> rows) {
        if (rows.isEmpty()) {
            return "NONE";
        }
        return rows.get(0).routeCode();
    }
}
