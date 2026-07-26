package com.archives.io;

import com.archives.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class TsvWriter {
    public void write(Path path, List<OutRow> rows) throws Exception {
        List<OutRow> sorted = new ArrayList<>(rows);
        sorted.sort(Comparator.comparing(OutRow::unitId));
        List<OutRow> unique = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (OutRow r : sorted) {
            if (seen.add(r.unitId())) {
                unique.add(r);
            }
        }
        List<String> lines = new ArrayList<>();
        lines.add("volume_id\tbranch_id\tcustody_class\trequest_qty");
        for (OutRow r : unique) {
            lines.add(String.format("%s\t%s\t%s\t%d", r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.write(path, lines);
    }
}
