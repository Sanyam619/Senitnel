package com.distro.io;

import com.distro.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class TsvWriter {
    public void write(Path path, List<OutRow> rows) throws Exception {
        List<OutRow> sorted = new ArrayList<>(rows);
        sorted.sort(Comparator.comparing(OutRow::unitId));
        List<String> lines = new ArrayList<>();
        lines.add("unit_id\tstore_id\texposure_class\tqty_cases");
        for (OutRow r : sorted) {
            lines.add(String.format("%s\t%s\t%s\t%d", r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.write(path, lines);
    }
}
