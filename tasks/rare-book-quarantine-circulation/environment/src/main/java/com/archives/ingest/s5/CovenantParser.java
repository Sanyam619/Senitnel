package com.archives.ingest.s5;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class CovenantParser {
    public List<CovenantRow> read(Path path) throws Exception {
        List<CovenantRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new CovenantRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
