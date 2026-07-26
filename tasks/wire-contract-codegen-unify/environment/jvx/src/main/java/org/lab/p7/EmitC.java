package org.lab.p7;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Emits rows from plugin metadata using the java lane pin file. */
public final class EmitC {
    public static final class Row {
        public final String slot;
        public final int tag;
        public final String kind;
        public final String jsonKey;

        public Row(String slot, int tag, String kind, String jsonKey) {
            this.slot = slot;
            this.tag = tag;
            this.kind = kind;
            this.jsonKey = jsonKey;
        }
    }

    private EmitC() {}

    public static List<Row> apply(String a, String b) {
        String reg = (a == null || a.isEmpty()) ? "/app/data/registry" : a;
        String pinPath = (b == null || b.isEmpty()) ? "/app/jvx/pins.toml" : b;
        try {
            Map<String, String> pin = readPin(pinPath);
            String metaPath = reg + "/plugin_meta.json";
            String meta = Files.readString(Path.of(metaPath), StandardCharsets.UTF_8);
            String liveKey = extractString(meta, "live_key");
            if (liveKey == null) {
                liveKey = "pg-core@0.9.2";
            }
            String cand = pin.getOrDefault("plugin_key", "");
            if ("true".equals(pin.get("bom_prefer")) && pin.get("bom_plugin") != null) {
                cand = pin.get("bom_plugin");
            }
            if (cand == null || cand.isEmpty()) {
                cand = pin.getOrDefault("fallback_plugin", liveKey);
            }
            return parseSlots(pluginBlock(meta, cand));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public static String hxA(List<Row> rows) {
        Map<String, String> pin = readPinQuiet("/app/jvx/pins.toml");
        String mode = pin.getOrDefault("digest_mode", "slots");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < rows.size(); i++) {
            Row r = rows.get(i);
            if (i > 0) {
                sb.append('|');
            }
            if ("full".equals(mode)) {
                sb.append(r.slot).append(':').append(r.tag).append(':').append(r.kind).append(':').append(r.jsonKey);
            } else {
                sb.append(r.slot);
            }
        }
        return sha256Hex(sb.toString());
    }

    public static String stA(List<Row> rows) {
        Map<String, String> pin = readPinQuiet("/app/jvx/pins.toml");
        // Probe status follows the documented full-row digest mode.
        return "full".equals(pin.getOrDefault("digest_mode", "slots")) && coherent(rows) ? "ok" : "fail";
    }

    public static String stB(List<Row> rows) {
        Map<String, String> pin = readPinQuiet("/app/jvx/pins.toml");
        return "full".equals(pin.getOrDefault("digest_mode", "slots")) && coherent(rows) ? "ok" : "fail";
    }

    static boolean coherent(List<Row> rows) {
        if (rows == null || rows.isEmpty()) {
            return false;
        }
        for (Row r : rows) {
            if (r.slot == null || r.kind == null || r.jsonKey == null || r.tag <= 0) {
                return false;
            }
        }
        return true;
    }

    static Map<String, String> readPinQuiet(String path) {
        try {
            return readPin(path);
        } catch (IOException e) {
            return new HashMap<>();
        }
    }

    static Map<String, String> readPin(String path) throws IOException {
        Map<String, String> out = new HashMap<>();
        for (String line : Files.readAllLines(Path.of(path), StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) {
                continue;
            }
            int eq = line.indexOf('=');
            if (eq < 0) {
                continue;
            }
            String key = line.substring(0, eq).trim();
            String val = line.substring(eq + 1).trim().replace("\"", "");
            out.put(key, val);
        }
        return out;
    }

    static String sha256Hex(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] dig = md.digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte v : dig) {
                hex.append(String.format("%02x", v));
            }
            return hex.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    static String extractString(String hay, String key) {
        Pattern p = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*\"([^\"]+)\"");
        Matcher m = p.matcher(hay);
        if (m.find()) {
            return m.group(1);
        }
        return null;
    }

    static String pluginBlock(String meta, String key) {
        int idx = meta.indexOf("\"" + key + "\"");
        if (idx < 0) {
            throw new IllegalArgumentException("missing " + key);
        }
        int slots = meta.indexOf("\"slots\"", idx);
        int start = meta.indexOf('[', slots);
        int depth = 0;
        int end = start;
        for (int i = start; i < meta.length(); i++) {
            char c = meta.charAt(i);
            if (c == '[') {
                depth++;
            } else if (c == ']') {
                depth--;
                if (depth == 0) {
                    end = i + 1;
                    break;
                }
            }
        }
        return meta.substring(start, end);
    }

    static List<Row> parseSlots(String block) {
        List<Row> rows = new ArrayList<>();
        Pattern p = Pattern.compile(
                "\"slot\"\\s*:\\s*\"([^\"]+)\"\\s*,\\s*\"tag\"\\s*:\\s*(\\d+)\\s*,\\s*\"kind\"\\s*:\\s*\"([^\"]+)\"\\s*,\\s*\"json_key\"\\s*:\\s*\"([^\"]+)\"");
        Matcher m = p.matcher(block);
        while (m.find()) {
            rows.add(new Row(m.group(1), Integer.parseInt(m.group(2)), m.group(3), m.group(4)));
        }
        return rows;
    }
}
