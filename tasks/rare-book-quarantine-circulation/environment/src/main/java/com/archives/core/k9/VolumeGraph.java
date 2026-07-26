package com.archives.core.k9;

import com.archives.ingest.d4.CirculationRow;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class VolumeGraph {
    public Map<String, List<String>> splitsFromCirculation(List<CirculationRow> dockRows) {
        Map<String, List<String>> out = new HashMap<>();
        for (CirculationRow row : dockRows) {
            if (row.parentId() != null && !row.parentId().isBlank()) {
                out.computeIfAbsent(row.parentId(), k -> new ArrayList<>()).add(row.unitId());
            }
        }
        return out;
    }
}
