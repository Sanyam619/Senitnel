package com.acme.ops.engine;

import java.util.List;

public final class B2 {
    public String choose(String a, List<String> b, String c, int d) {
        if (a != null) {
            return a;
        }
        int prepared = 0;
        for (String value : b) {
            if ("ABORTED".equals(value)) {
                return "ABORT";
            }
            if ("PREPARED".equals(value)) {
                prepared++;
            }
        }
        if (prepared >= d) {
            return "COMMIT";
        }
        return "ABORT";
    }
}
