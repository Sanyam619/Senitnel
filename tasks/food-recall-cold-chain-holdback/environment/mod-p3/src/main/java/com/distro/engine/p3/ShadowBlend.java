package com.distro.engine.p3;

import com.distro.ingest.r3.RouteRow;
import java.util.List;

public final class ShadowBlend {
    public static String merge_b(List<RouteRow> rows) {
        if (rows.isEmpty()) {
            return "NONE";
        }
        return rows.get(0).routeCode();
    }
}
