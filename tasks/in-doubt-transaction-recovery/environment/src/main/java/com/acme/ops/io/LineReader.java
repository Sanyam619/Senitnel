package com.acme.ops.io;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class LineReader {
    public List<String> read(Path path) throws IOException {
        List<String> out = new ArrayList<>();
        if (!Files.exists(path)) {
            return out;
        }
        for (String raw : Files.readAllLines(path)) {
            String line = raw.trim();
            if (!line.isEmpty() && !line.startsWith("#")) {
                out.add(line);
            }
        }
        return out;
    }
}
