#!/usr/bin/env bash
set -euo pipefail

cd /opt/archives

cat > src/main/java/com/archives/engine/p3/MergeLane.java <<'JAVA'
package com.archives.engine.p3;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.s5.CovenantRow;
import com.archives.ingest.v6.ExhibitRow;

public final class MergeLane {
    private static boolean activeFlag(QuarantineRow a) {
        return a != null && "ACTIVE".equals(a.severity());
    }

    private static boolean covenantGrant(CovenantRow b) {
        return b != null && "GRANT".equals(b.decision());
    }

    private static boolean exhibitClear(ExhibitRow c) {
        return c != null && "CLEARED_FOR_EXHIBIT".equals(c.status());
    }

    public static String merge_b(QuarantineRow a, CovenantRow b, ExhibitRow c) {
        if (activeFlag(a)) {
            if (exhibitClear(c) && covenantGrant(b)) {
                return "ALLOW";
            }
            return "DENIED_LOAN";
        }
        if (covenantGrant(b)) {
            return "ALLOW";
        }
        if (exhibitClear(c)) {
            return "ALLOW";
        }
        return "ALLOW";
    }

    public static int rank(CovenantRow b, QuarantineRow a) {
        if (activeFlag(a)) {
            return 1;
        }
        return b == null ? 99 : 5;
    }
}
JAVA

cat > src/main/java/com/archives/ingest/m7/RfidFold.java <<'JAVA'
package com.archives.ingest.m7;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class RfidFold {
    public static List<RfidRow> read(Path path) throws Exception {
        List<RfidRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new RfidRow(cols[0], Long.parseLong(cols[1]), Integer.parseInt(cols[2])));
        }
        return rows;
    }

    public static List<RfidRow> collapseLatest(List<RfidRow> rows) {
        Map<String, RfidRow> latest = new LinkedHashMap<>();
        for (RfidRow row : rows) {
            latest.put(row.unitId(), row);
        }
        return new ArrayList<>(latest.values());
    }

    public static List<RfidRow> fold_a(List<RfidRow> rows, long x, long y) {
        List<RfidRow> out = new ArrayList<>();
        for (RfidRow r : rows) {
            if (r.ts() >= x && r.ts() <= y) {
                out.add(r);
            }
        }
        return collapseLatest(out);
    }
}
JAVA

cat > src/main/java/com/archives/core/k9/LineageExpand.java <<'JAVA'
package com.archives.core.k9;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Map;

public final class LineageExpand {
    public static List<String> walkAll(String root, Map<String, List<String>> m) {
        List<String> out = new ArrayList<>();
        Deque<String> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            String cur = queue.removeFirst();
            List<String> kids = m.get(cur);
            if (kids == null || kids.isEmpty()) {
                out.add(cur);
                continue;
            }
            for (String kid : kids) {
                queue.addLast(kid);
            }
        }
        return out;
    }

    public static List<String> resolve_d(String p, Map<String, List<String>> m) {
        List<String> kids = m.get(p);
        if (kids == null || kids.isEmpty()) {
            return List.of(p);
        }
        return new ArrayList<>(kids);
    }

    public static List<String> expandAll(String p, Map<String, List<String>> m) {
        return new ArrayList<>(walkAll(p, m));
    }
}
JAVA

cat > src/main/java/com/archives/io/TsvWriter.java <<'JAVA'
package com.archives.io;

import com.archives.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class TsvWriter {
    public void write(Path path, List<OutRow> rows) throws Exception {
        List<OutRow> sorted = new ArrayList<>(rows);
        sorted.sort(Comparator.comparing(OutRow::unitId).thenComparing(OutRow::stateOrStore));
        List<String> lines = new ArrayList<>();
        lines.add("volume_id\tbranch_id\tcustody_class\trequest_qty");
        for (OutRow r : sorted) {
            lines.add(String.format("%s\t%s\t%s\t%d", r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.write(path, lines);
    }
}
JAVA

mvn -o -q package
cp target/circulation-batch-1.0.0.jar /opt/archives/target/circulation-batch-1.0.0.jar

for day in day_c0901 day_c0902 day_c0903 day_c0904 day_c0906; do
  /opt/archives/scripts/run-cycle.sh --day "$day" --root /data/fixtures
done
