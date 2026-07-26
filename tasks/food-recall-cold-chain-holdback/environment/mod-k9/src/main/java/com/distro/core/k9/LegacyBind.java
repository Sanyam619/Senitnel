package com.distro.core.k9;

import java.util.HashMap;
import java.util.Map;

public final class LegacyBind {
    public Map<String, String> resolve_d(String legacyId) {
        Map<String, String> m = new HashMap<>();
        m.put(legacyId, "WH-" + legacyId);
        return m;
    }
}
