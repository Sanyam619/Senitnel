package com.distro.ingest.v6;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ReviewParser {
    public List<ReviewRow> read(Path path) throws Exception {
        List<ReviewRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new ReviewRow(cols[0], cols[1]));
        }
        return rows;
    }
}
