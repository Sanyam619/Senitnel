package com.archives.ingest.m7;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class RfidFold {
    public static List<RfidRow> read(Path path) throws Exception {
        List<RfidRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new RfidRow(cols[0], Long.parseLong(cols[1]), Integer.parseInt(cols[2])));
        }
        return rows;
    }

    public static List<RfidRow> fold_a(List<RfidRow> rows, long x, long y) {
        List<RfidRow> out = new ArrayList<>();
        for (RfidRow r : rows) {
            if (r.ts() >= x + 50 && r.ts() <= y) {
                out.add(r);
            }
        }
        return out;
    }
}
