package com.acme.ops.io;

import java.util.Iterator;
import java.util.List;
import java.util.Map;

public final class JsonWriter {
    public String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch == '"' || ch == '\\') {
                out.append('\\').append(ch);
            } else if (ch == '\n') {
                out.append("\\n");
            } else {
                out.append(ch);
            }
        }
        return out.append('"').toString();
    }

    public String array(List<String> values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.size(); i++) {
            if (i > 0) {
                out.append(",");
            }
            out.append(quote(values.get(i)));
        }
        return out.append("]").toString();
    }

    public <T> void appendEntries(StringBuilder out, Map<String, T> map, Appender<T> appender) {
        Iterator<Map.Entry<String, T>> it = map.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, T> entry = it.next();
            out.append(quote(entry.getKey())).append(":");
            appender.append(out, entry.getValue());
            if (it.hasNext()) {
                out.append(",");
            }
        }
    }

    public interface Appender<T> {
        void append(StringBuilder out, T value);
    }
}
