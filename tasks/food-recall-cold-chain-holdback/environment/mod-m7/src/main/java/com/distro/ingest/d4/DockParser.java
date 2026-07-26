package com.distro.ingest.d4;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class DockParser {
    public List<DockRow> read(Path path) throws Exception {
        List<DockRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            String parent = cols.length > 3 && !cols[3].isBlank() ? cols[3] : null;
            rows.add(new DockRow(cols[0], cols[1], Integer.parseInt(cols[2]), parent));
        }
        return rows;
    }
}
