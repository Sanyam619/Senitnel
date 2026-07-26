package com.archives.core.k9;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class LineageExpand {
    public static List<String> resolve_d(String p, Map<String, List<String>> m) {
        List<String> kids = m.get(p);
        if (kids == null || kids.isEmpty()) {
            return List.of(p);
        }
        return List.of(kids.get(0));
    }

    public static List<String> expandAll(String p, Map<String, List<String>> m) {
        return new ArrayList<>(resolve_d(p, m));
    }
}
