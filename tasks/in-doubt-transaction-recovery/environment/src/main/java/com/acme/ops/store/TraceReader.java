package com.acme.ops.store;

import com.acme.ops.io.LineReader;
import com.acme.ops.model.ActionRecord;
import com.acme.ops.model.Bundle;
import com.acme.ops.model.UnitRecord;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.TreeMap;
import java.util.stream.Collectors;

public final class TraceReader {
    private final LineReader lineReader = new LineReader();
    private final EventTape tape = new EventTape();

    public Map<String, Bundle> load(Path root) throws IOException {
        Map<String, Bundle> out = new TreeMap<>();
        try (var stream = Files.list(root)) {
            for (Path dir : stream.filter(Files::isDirectory).sorted().collect(Collectors.toList())) {
                Bundle bundle = one(dir);
                out.put(bundle.name(), bundle);
            }
        }
        return out;
    }

    private Bundle one(Path dir) throws IOException {
        Properties meta = new Properties();
        try (var input = Files.newInputStream(dir.resolve("meta.properties"))) {
            meta.load(input);
        }
        String mode = meta.getProperty("mode", "PA").trim();
        List<String> members = List.of(meta.getProperty("members", "").split(",")).stream()
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .collect(Collectors.toList());
        Map<String, String> rows = new LinkedHashMap<>();
        for (String line : lineReader.read(dir.resolve("coordinator.log"))) {
            String[] parts = line.split("\\s+");
            if (parts.length >= 4 && "TX".equals(parts[0]) && "DECISION".equals(parts[2])) {
                rows.put(parts[1], parts[3]);
            }
        }
        List<UnitRecord> units = new ArrayList<>();
        for (String member : members) {
            units.addAll(tape.units(member, lineReader.read(dir.resolve("member-" + member + ".log"))));
        }
        return new Bundle(dir.getFileName().toString(), mode, members, rows, units, actions(dir.resolve("saga.plan")));
    }

    private List<ActionRecord> actions(Path path) throws IOException {
        List<ActionRecord> out = new ArrayList<>();
        String group = "";
        String id = "";
        for (String line : lineReader.read(path)) {
            String[] parts = line.split("\\s+");
            if (parts.length >= 4 && "SAGA".equals(parts[0])) {
                group = parts[1];
                id = parts[3];
            } else if (parts.length >= 4 && "STEP".equals(parts[0])) {
                out.add(new ActionRecord(group, id, parts[1], parts[2], parts[3]));
            }
        }
        return out;
    }
}
