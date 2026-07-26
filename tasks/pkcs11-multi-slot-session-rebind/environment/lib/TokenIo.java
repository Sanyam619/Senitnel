package lib;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class TokenIo {
    private TokenIo() {}

    public static String readText(Path p) throws IOException {
        return Files.readString(p, StandardCharsets.UTF_8);
    }

    public static void writeText(Path p, String body) throws IOException {
        Files.createDirectories(p.getParent());
        Files.writeString(p, body, StandardCharsets.UTF_8);
    }

    public static List<Map<String, String>> readInventory(Path root) throws IOException {
        List<Map<String, String>> rows = new ArrayList<>();
        Path inv = root.resolve("inventory.txt");
        for (String line : Files.readAllLines(inv, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] parts = line.split("\\s+");
            if (parts.length < 2) continue;
            Map<String, String> m = new HashMap<>();
            m.put("id", parts[0]);
            m.put("role", parts[1]);
            if (parts.length >= 3) {
                m.put("epoch", parts[2]);
            }
            rows.add(m);
        }
        return rows;
    }

    public static List<String> readLabels(Path root) throws IOException {
        List<String> out = new ArrayList<>();
        Path p = root.resolve("labels.txt");
        for (String line : Files.readAllLines(p, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            out.add(line);
        }
        return out;
    }

    public static int readBound(Path root) throws IOException {
        Path p = root.resolve("provider.txt");
        for (String line : Files.readAllLines(p, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.startsWith("bound=")) {
                return Integer.parseInt(line.substring("bound=".length()).trim());
            }
        }
        return -1;
    }

    public static int readBoundFromFile(Path file) throws IOException {
        for (String line : Files.readAllLines(file, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.startsWith("bound=")) {
                return Integer.parseInt(line.substring("bound=".length()).trim());
            }
        }
        return -1;
    }

    public static void writeBound(Path root, int id) throws IOException {
        writeText(root.resolve("provider.txt"), "bound=" + id + "\n");
    }

    public static List<Map<String, String>> readObjects(Path root) throws IOException {
        List<Map<String, String>> rows = new ArrayList<>();
        Path p = root.resolve("objects.txt");
        for (String line : Files.readAllLines(p, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] parts = line.split("\\s+");
            if (parts.length < 3) continue;
            Map<String, String> m = new HashMap<>();
            m.put("label", parts[0]);
            m.put("slot_id", parts[1]);
            m.put("handle", parts[2]);
            rows.add(m);
        }
        return rows;
    }

    public static List<Map<String, String>> readSessions(Path root) throws IOException {
        List<Map<String, String>> rows = new ArrayList<>();
        Path p = root.resolve("sessions.txt");
        for (String line : Files.readAllLines(p, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] parts = line.split("\\s+");
            if (parts.length < 3) continue;
            Map<String, String> m = new HashMap<>();
            m.put("slot_id", parts[0]);
            m.put("pin_alive", parts[1]);
            m.put("ttl_sec", parts[2]);
            rows.add(m);
        }
        return rows;
    }

    public static void writeSessions(Path root, List<Map<String, String>> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("# slot pin_alive ttl\n");
        for (Map<String, String> m : rows) {
            sb.append(m.get("slot_id")).append(' ')
                    .append(m.get("pin_alive")).append(' ')
                    .append(m.get("ttl_sec")).append('\n');
        }
        writeText(root.resolve("sessions.txt"), sb.toString());
    }

    public static int readPolicyTtl(Path policy) throws IOException {
        for (String line : Files.readAllLines(policy, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.startsWith("ttl_sec")) {
                String[] parts = line.split("=", 2);
                if (parts.length == 2) {
                    return Integer.parseInt(parts[1].trim());
                }
            }
        }
        return 300;
    }
}
