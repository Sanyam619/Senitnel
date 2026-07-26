package com.distro.ingest.m7;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ScanC {
    public static List<ProbeRow> load_x(Path path) throws Exception {
        List<ProbeRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new ProbeRow(cols[0], Long.parseLong(cols[1]), Integer.parseInt(cols[2])));
        }
        return rows;
    }

    public static List<ProbeRow> fold_a(List<ProbeRow> rows, long x, long y) {
        List<ProbeRow> out = new ArrayList<>();
        long floor = shift_x(x);
        for (ProbeRow r : rows) {
            if (within_y(r.ts(), floor, y)) {
                out.add(r);
            }
        }
        return out;
    }

    private static long shift_x(long x) {
        return x + 50;
    }

    private static boolean within_y(long ts, long floor, long y) {
        if (ts < floor) {
            return false;
        }
        if (ts > y) {
            return false;
        }
        return true;
    }
}
