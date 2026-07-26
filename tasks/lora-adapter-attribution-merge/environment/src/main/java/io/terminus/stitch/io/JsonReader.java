package io.terminus.stitch.io;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Minimal JSON parser sufficient for the pipeline's dataset and reports.
 *  Supports objects, arrays, doubles, ints, booleans, null, strings. */
public final class JsonReader {
    private final String src;
    private int pos;

    public JsonReader(String src) {
        this.src = src;
        this.pos = 0;
    }

    public static Object parse(String src) {
        JsonReader r = new JsonReader(src);
        r.skipWs();
        Object v = r.readValue();
        r.skipWs();
        if (r.pos != r.src.length()) {
            throw new RuntimeException("trailing data at pos " + r.pos);
        }
        return v;
    }

    private Object readValue() {
        skipWs();
        if (pos >= src.length()) throw new RuntimeException("EOF");
        char c = src.charAt(pos);
        if (c == '{') return readObject();
        if (c == '[') return readArray();
        if (c == '"') return readString();
        if (c == 't' || c == 'f') return readBool();
        if (c == 'n') { expect("null"); return null; }
        return readNumber();
    }

    private Map<String, Object> readObject() {
        LinkedHashMap<String, Object> m = new LinkedHashMap<>();
        expect("{");
        skipWs();
        if (peek() == '}') { pos++; return m; }
        while (true) {
            skipWs();
            String key = readString();
            skipWs();
            expect(":");
            Object v = readValue();
            m.put(key, v);
            skipWs();
            char c = src.charAt(pos);
            if (c == ',') { pos++; continue; }
            if (c == '}') { pos++; return m; }
            throw new RuntimeException("expected , or } at " + pos);
        }
    }

    private List<Object> readArray() {
        List<Object> a = new ArrayList<>();
        expect("[");
        skipWs();
        if (peek() == ']') { pos++; return a; }
        while (true) {
            Object v = readValue();
            a.add(v);
            skipWs();
            char c = src.charAt(pos);
            if (c == ',') { pos++; continue; }
            if (c == ']') { pos++; return a; }
            throw new RuntimeException("expected , or ] at " + pos);
        }
    }

    private String readString() {
        expect("\"");
        StringBuilder sb = new StringBuilder();
        while (pos < src.length()) {
            char c = src.charAt(pos++);
            if (c == '"') return sb.toString();
            if (c == '\\') {
                char e = src.charAt(pos++);
                switch (e) {
                    case '"':  sb.append('"'); break;
                    case '\\': sb.append('\\'); break;
                    case '/':  sb.append('/'); break;
                    case 'n':  sb.append('\n'); break;
                    case 't':  sb.append('\t'); break;
                    case 'r':  sb.append('\r'); break;
                    case 'b':  sb.append('\b'); break;
                    case 'f':  sb.append('\f'); break;
                    case 'u':
                        int code = Integer.parseInt(src.substring(pos, pos + 4), 16);
                        sb.append((char) code);
                        pos += 4;
                        break;
                    default: throw new RuntimeException("bad escape \\" + e);
                }
            } else {
                sb.append(c);
            }
        }
        throw new RuntimeException("unterminated string");
    }

    private Boolean readBool() {
        if (src.startsWith("true", pos)) { pos += 4; return true; }
        if (src.startsWith("false", pos)) { pos += 5; return false; }
        throw new RuntimeException("bad bool at " + pos);
    }

    private Number readNumber() {
        int start = pos;
        if (peek() == '-' || peek() == '+') pos++;
        boolean isDouble = false;
        while (pos < src.length()) {
            char c = src.charAt(pos);
            if ((c >= '0' && c <= '9') || c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-') {
                if (c == '.' || c == 'e' || c == 'E') isDouble = true;
                pos++;
            } else break;
        }
        String s = src.substring(start, pos);
        if (isDouble) return Double.parseDouble(s);
        try {
            return Long.parseLong(s);
        } catch (NumberFormatException ex) {
            return Double.parseDouble(s);
        }
    }

    private void skipWs() {
        while (pos < src.length()) {
            char c = src.charAt(pos);
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') pos++;
            else break;
        }
    }

    private char peek() {
        return src.charAt(pos);
    }

    private void expect(String s) {
        if (!src.startsWith(s, pos)) {
            throw new RuntimeException("expected '" + s + "' at " + pos);
        }
        pos += s.length();
    }

    // Convenience helpers used by callers.

    @SuppressWarnings("unchecked")
    public static Map<String, Object> asObject(Object v) { return (Map<String, Object>) v; }

    @SuppressWarnings("unchecked")
    public static List<Object> asArray(Object v) { return (List<Object>) v; }

    public static double asDouble(Object v) {
        if (v instanceof Long) return ((Long) v).doubleValue();
        return ((Number) v).doubleValue();
    }

    public static int asInt(Object v) {
        if (v instanceof Long) return ((Long) v).intValue();
        return ((Number) v).intValue();
    }

    public static long asLong(Object v) {
        return ((Number) v).longValue();
    }

    public static String asString(Object v) { return (String) v; }

    /** Convert a JSON array-of-arrays into a double[][]. */
    public static double[][] asMatrix(Object v) {
        List<Object> outer = asArray(v);
        int rows = outer.size();
        int cols = asArray(outer.get(0)).size();
        double[][] m = new double[rows][cols];
        for (int i = 0; i < rows; i++) {
            List<Object> row = asArray(outer.get(i));
            for (int j = 0; j < cols; j++) {
                m[i][j] = asDouble(row.get(j));
            }
        }
        return m;
    }

    /** Convert a JSON array-of-ints into an int[]. */
    public static int[] asIntArray(Object v) {
        List<Object> outer = asArray(v);
        int[] out = new int[outer.size()];
        for (int i = 0; i < outer.size(); i++) out[i] = asInt(outer.get(i));
        return out;
    }
}
