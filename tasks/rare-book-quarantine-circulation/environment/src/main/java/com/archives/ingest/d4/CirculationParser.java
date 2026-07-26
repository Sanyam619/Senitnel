package com.archives.ingest.d4;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class CirculationParser {
    public List<CirculationRow> read(Path path) throws Exception {
        List<CirculationRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            String parent = cols.length > 3 && !cols[3].isBlank() ? cols[3] : null;
            rows.add(new CirculationRow(cols[0], cols[1], Integer.parseInt(cols[2]), parent));
        }
        return rows;
    }
}
