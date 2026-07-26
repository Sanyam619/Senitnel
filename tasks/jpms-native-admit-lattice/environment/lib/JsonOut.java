package lib;

import java.io.IOException;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;

public final class JsonOut {
    private JsonOut() {}

    public static void writeLedger(int bindEpoch, List<Map<String, String>> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"schema_version\": \"pack-admit-1\",\n");
        sb.append("  \"bind_epoch\": ").append(bindEpoch).append(",\n");
        sb.append("  \"rows\": [\n");
        for (int i = 0; i < rows.size(); i++) {
            Map<String, String> r = rows.get(i);
            sb.append("    {");
            sb.append("\"id\": \"").append(r.get("id")).append("\", ");
            sb.append("\"decision\": \"").append(r.get("decision")).append("\", ");
            sb.append("\"reason_code\": \"").append(r.get("reason_code")).append("\"");
            sb.append("}");
            if (i + 1 < rows.size()) {
                sb.append(",");
            }
            sb.append("\n");
        }
        sb.append("  ]\n");
        sb.append("}\n");
        Files.createDirectories(Paths.OUTPUT.getParent());
        Files.writeString(Paths.OUTPUT, sb.toString());
    }
}
