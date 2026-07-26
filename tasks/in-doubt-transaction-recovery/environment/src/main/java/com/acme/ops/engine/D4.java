package com.acme.ops.engine;

import com.acme.ops.model.ActionRecord;
import com.acme.ops.model.Bundle;
import com.acme.ops.model.RepairRecord;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class D4 {
    public List<RepairRecord> make(Bundle x, Map<String, String> y) {
        Map<String, List<ActionRecord>> byGroup = new LinkedHashMap<>();
        for (ActionRecord action : x.actions()) {
            byGroup.computeIfAbsent(action.group(), k -> new ArrayList<>()).add(action);
        }
        List<RepairRecord> out = new ArrayList<>();
        for (Map.Entry<String, List<ActionRecord>> item : byGroup.entrySet()) {
            out.add(new RepairRecord(item.getKey(), ""));
            for (ActionRecord action : item.getValue()) {
                if (!"COMMIT".equals(y.get(action.group())) && !"PENDING".equals(action.state())) {
                    out.add(new RepairRecord(action.group(), action.label()));
                }
            }
        }
        return out;
    }
}
