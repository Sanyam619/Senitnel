package com.archives.io;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class JsonReader {
    public static Map<String, Object> readObject(Path path) throws Exception {
        String raw = Files.readString(path).trim();
        Map<String, Object> out = new HashMap<>();
        Matcher hook = Pattern.compile("\"sweep_start_ts\"\\s*:\\s*(\\d+)").matcher(raw);
        Matcher dock = Pattern.compile("\"sweep_end_ts\"\\s*:\\s*(\\d+)").matcher(raw);
        if (hook.find()) {
            out.put("sweep_start_ts", Long.parseLong(hook.group(1)));
        }
        if (dock.find()) {
            out.put("sweep_end_ts", Long.parseLong(dock.group(1)));
        }
        List<String> units = new ArrayList<>();
        Matcher unit = Pattern.compile("\"(VOL-[A-Z0-9]+)\"").matcher(raw);
        while (unit.find()) {
            units.add(unit.group(1));
        }
        out.put("units", units);
        return out;
    }
}
