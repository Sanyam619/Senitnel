package io.terminus.stitch.io;

import java.util.List;
import java.util.Map;

/** Minimal JSON writer with deterministic key order and consistent number
 *  formatting. Used for the merge report and for fixture generation. */
public final class JsonWriter {
    private final StringBuilder sb = new StringBuilder(4096);
    private int indent = 0;

    public String toString() { return sb.toString(); }

    public JsonWriter writeAny(Object v) {
        if (v == null) { sb.append("null"); return this; }
        if (v instanceof Map) return writeObject((Map<String, Object>) v);
        if (v instanceof List) return writeArray((List<Object>) v);
        if (v instanceof String) return writeString((String) v);
        if (v instanceof Boolean) { sb.append(((Boolean) v) ? "true" : "false"); return this; }
        if (v instanceof Double || v instanceof Float) return writeDouble(((Number) v).doubleValue());
        if (v instanceof Number) { sb.append(((Number) v).longValue()); return this; }
        if (v instanceof double[][]) return writeMatrix((double[][]) v);
        if (v instanceof double[]) return writeDoubleArray((double[]) v);
        if (v instanceof int[]) return writeIntArray((int[]) v);
        throw new RuntimeException("unsupported json value type: " + v.getClass());
    }

    private JsonWriter writeObject(Map<String, Object> m) {
        if (m.isEmpty()) { sb.append("{}"); return this; }
        sb.append("{\n");
        indent++;
        int i = 0;
        for (Map.Entry<String, Object> e : m.entrySet()) {
            pad();
            writeString(e.getKey());
            sb.append(": ");
            writeAny(e.getValue());
            if (i < m.size() - 1) sb.append(',');
            sb.append('\n');
            i++;
        }
        indent--;
        pad();
        sb.append('}');
        return this;
    }

    private JsonWriter writeArray(List<Object> a) {
        if (a.isEmpty()) { sb.append("[]"); return this; }
        sb.append("[\n");
        indent++;
        for (int i = 0; i < a.size(); i++) {
            pad();
            writeAny(a.get(i));
            if (i < a.size() - 1) sb.append(',');
            sb.append('\n');
        }
        indent--;
        pad();
        sb.append(']');
        return this;
    }

    public JsonWriter writeMatrix(double[][] m) {
        sb.append("[");
        for (int i = 0; i < m.length; i++) {
            if (i > 0) sb.append(", ");
            writeDoubleArray(m[i]);
        }
        sb.append("]");
        return this;
    }

    public JsonWriter writeDoubleArray(double[] arr) {
        sb.append("[");
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) sb.append(", ");
            writeDouble(arr[i]);
        }
        sb.append("]");
        return this;
    }

    public JsonWriter writeIntArray(int[] arr) {
        sb.append("[");
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) sb.append(", ");
            sb.append(arr[i]);
        }
        sb.append("]");
        return this;
    }

    public JsonWriter writeDouble(double d) {
        if (Double.isNaN(d) || Double.isInfinite(d)) {
            throw new RuntimeException("cannot emit non-finite double: " + d);
        }
        // Use a stable decimal form with sufficient precision to round-trip.
        String s = String.format(java.util.Locale.ROOT, "%.17g", d);
        sb.append(s);
        return this;
    }

    public JsonWriter writeString(String s) {
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default:
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                    else sb.append(c);
            }
        }
        sb.append('"');
        return this;
    }

    private void pad() {
        for (int k = 0; k < indent; k++) sb.append("  ");
    }
}
