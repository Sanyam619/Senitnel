package com.archives.ingest.n2;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class QuarantineParser {
    public List<QuarantineRow> read(Path path) throws Exception {
        List<QuarantineRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new QuarantineRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
