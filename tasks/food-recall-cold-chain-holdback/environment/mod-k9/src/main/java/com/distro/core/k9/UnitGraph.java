package com.distro.core.k9;

import com.distro.ingest.d4.DockRow;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class UnitGraph {
    public Map<String, List<String>> splitsFromDock(List<DockRow> dockRows) {
        Map<String, List<String>> out = new HashMap<>();
        for (DockRow row : dockRows) {
            if (row.parentId() != null && !row.parentId().isBlank()) {
                out.computeIfAbsent(row.parentId(), k -> new ArrayList<>()).add(row.unitId());
            }
        }
        return out;
    }
}
