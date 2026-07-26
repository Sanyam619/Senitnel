package com.distro.ingest.n2;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class NoticeParser {
    public List<NoticeRow> read(Path path) throws Exception {
        List<NoticeRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new NoticeRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
