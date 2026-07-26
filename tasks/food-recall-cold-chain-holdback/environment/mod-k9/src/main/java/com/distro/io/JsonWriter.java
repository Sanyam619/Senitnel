package com.distro.io;

import com.distro.model.AuditEntry;
import com.distro.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public final class JsonWriter {
    public void writeLedger(Path path, List<OutRow> rows) throws Exception {
        StringBuilder sb = new StringBuilder();
        for (OutRow r : rows) {
            sb.append(String.format(
                "{\"unit_id\":\"%s\",\"state\":\"%s\",\"reason_code\":\"%s\",\"source_day\":%d}%n",
                r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.writeString(path, sb.toString());
    }

    public void writeAudit(Path path, List<AuditEntry> entries) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"version\":1,\"entries\":[");
        for (int i = 0; i < entries.size(); i++) {
            AuditEntry e = entries.get(i);
            if (i > 0) {
                sb.append(',');
            }
            sb.append(String.format(
                "{\"unit_id\":\"%s\",\"auth_id\":\"%s\",\"decision\":\"%s\",\"precedence_rank\":%d}",
                e.unitId(), e.authId(), e.decision(), e.precedenceRank()));
        }
        sb.append("]}");
        Files.writeString(path, sb.toString());
    }
}
