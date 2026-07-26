package com.archives.ingest.m7;

import java.util.ArrayList;
import java.util.List;

public final class SignalFold {
    public static double fold_a(List<Integer> samples) {
        if (samples.isEmpty()) {
            return 0.0;
        }
        int sum = 0;
        for (int v : samples) {
            sum += v;
        }
        return sum / (double) samples.size();
    }

    public static List<Integer> window(List<Integer> all, int start, int end) {
        List<Integer> out = new ArrayList<>();
        for (int i = start; i < end && i < all.size(); i++) {
            out.add(all.get(i));
        }
        return out;
    }
}
