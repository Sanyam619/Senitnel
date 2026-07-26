package com.archives.io;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class CsvReader {
    public static List<String[]> read(Path path) throws Exception {
        List<String[]> rows = new ArrayList<>();
        List<String> lines = Files.readAllLines(path);
        boolean first = true;
        for (String line : lines) {
            if (line.isBlank()) continue;
            if (first) { first = false; continue; }
            rows.add(line.split(",", -1));
        }
        return rows;
    }
}
