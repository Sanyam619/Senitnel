package com.distro.ingest.s5;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class SignoffParser {
    public List<SignoffRow> read(Path path) throws Exception {
        List<SignoffRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new SignoffRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
