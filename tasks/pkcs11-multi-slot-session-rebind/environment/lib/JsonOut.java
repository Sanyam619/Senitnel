package lib;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class JsonOut {
    private JsonOut() {}

    public static void writeLedger(
            Path out,
            List<Map<String, String>> slots,
            List<Map<String, String>> sessions,
            List<Map<String, String>> certs) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"version\": 1,\n");
        sb.append("  \"slots\": [\n");
        for (int i = 0; i < slots.size(); i++) {
            Map<String, String> s = slots.get(i);
            sb.append("    {\"id\": ").append(s.get("id"))
                    .append(", \"role\": \"").append(s.get("role")).append("\"")
                    .append(", \"provider_bound\": ").append(s.get("provider_bound"))
                    .append("}");
            if (i + 1 < slots.size()) sb.append(',');
            sb.append('\n');
        }
        sb.append("  ],\n");
        sb.append("  \"sessions\": [\n");
        for (int i = 0; i < sessions.size(); i++) {
            Map<String, String> s = sessions.get(i);
            sb.append("    {\"slot_id\": ").append(s.get("slot_id"))
                    .append(", \"pin_alive\": ").append(s.get("pin_alive"))
                    .append(", \"ttl_sec\": ").append(s.get("ttl_sec"))
                    .append("}");
            if (i + 1 < sessions.size()) sb.append(',');
            sb.append('\n');
        }
        sb.append("  ],\n");
        sb.append("  \"certs\": [\n");
        for (int i = 0; i < certs.size(); i++) {
            Map<String, String> c = certs.get(i);
            sb.append("    {\"label\": \"").append(c.get("label")).append("\"")
                    .append(", \"slot_id\": ").append(c.get("slot_id"))
                    .append(", \"handle_auth\": ").append(c.get("handle_auth"))
                    .append("}");
            if (i + 1 < certs.size()) sb.append(',');
            sb.append('\n');
        }
        sb.append("  ]\n");
        sb.append("}\n");
        TokenIo.writeText(out, sb.toString());
    }
}
