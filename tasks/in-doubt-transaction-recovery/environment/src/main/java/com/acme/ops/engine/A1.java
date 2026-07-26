package com.acme.ops.engine;

import com.acme.ops.model.Bundle;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;

public final class A1 {
    private final B2 b2 = new B2();
    private final C3 c3 = new C3();

    public Map<String, String> fold(Bundle x) {
        Map<String, java.util.List<String>> grouped = c3.collect(x);
        var ids = new TreeSet<String>();
        ids.addAll(x.rows().keySet());
        ids.addAll(grouped.keySet());
        Map<String, String> out = new TreeMap<>();
        for (String id : ids) {
            out.put(id, b2.choose(x.rows().get(id), grouped.getOrDefault(id, java.util.List.of()), x.mode(), x.members().size()));
        }
        return out;
    }
}
