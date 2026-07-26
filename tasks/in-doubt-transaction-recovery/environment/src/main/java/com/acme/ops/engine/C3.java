package com.acme.ops.engine;

import com.acme.ops.model.Bundle;
import com.acme.ops.model.UnitRecord;
import java.util.ArrayList;
import java.util.Map;
import java.util.TreeMap;

public final class C3 {
    public Map<String, java.util.List<String>> collect(Bundle x) {
        Map<String, String> tail = new TreeMap<>();
        for (UnitRecord unit : x.units()) {
            tail.put(unit.id(), unit.state());
        }
        Map<String, java.util.List<String>> out = new TreeMap<>();
        for (Map.Entry<String, String> item : tail.entrySet()) {
            out.put(item.getKey(), new ArrayList<>(java.util.List.of(item.getValue())));
        }
        return out;
    }
}
