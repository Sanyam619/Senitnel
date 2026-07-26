package com.archives.ingest.v6;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ExhibitParser {
    public List<ExhibitRow> read(Path path) throws Exception {
        List<ExhibitRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new ExhibitRow(cols[0], cols[1]));
        }
        return rows;
    }
}
