package com.acme.ops.store;

import com.acme.ops.model.UnitRecord;
import java.util.ArrayList;
import java.util.List;

public final class EventTape {
    public List<UnitRecord> units(String source, List<String> lines) {
        List<UnitRecord> out = new ArrayList<>();
        for (String line : lines) {
            String[] parts = line.split("\\s+");
            if (parts.length >= 3 && "TX".equals(parts[0])) {
                out.add(new UnitRecord(source, parts[1], parts[2]));
            }
        }
        return out;
    }
}
