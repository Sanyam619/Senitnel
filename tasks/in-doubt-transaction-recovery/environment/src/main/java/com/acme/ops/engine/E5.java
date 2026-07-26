package com.acme.ops.engine;

import com.acme.ops.io.JsonWriter;
import com.acme.ops.model.RepairRecord;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class E5 {
    private final JsonWriter json = new JsonWriter();

    public void emit(Path a, Map<String, Map<String, String>> b, Map<String, List<RepairRecord>> c) throws IOException {
        Files.createDirectories(a);
        Files.writeString(a.resolve("decisions.json"), decisions(b));
        Files.writeString(a.resolve("compensations.json"), repairs(c));
    }

    private String decisions(Map<String, Map<String, String>> data) {
        StringBuilder out = new StringBuilder("{\"scenarios\":{");
        json.appendEntries(out, new TreeMap<>(data), (scenarioOut, txs) -> {
            scenarioOut.append("{\"transactions\":{");
            json.appendEntries(scenarioOut, new TreeMap<>(txs), (txOut, value) ->
                    txOut.append("{\"decision\":").append(json.quote(value)).append("}"));
            scenarioOut.append("}}");
        });
        return out.append("}}\n").toString();
    }

    private String repairs(Map<String, List<RepairRecord>> data) {
        Map<String, Map<String, List<String>>> grouped = new TreeMap<>();
        for (Map.Entry<String, List<RepairRecord>> entry : data.entrySet()) {
            Map<String, List<String>> byGroup = new TreeMap<>();
            for (RepairRecord record : entry.getValue()) {
                List<String> labels = byGroup.computeIfAbsent(record.group(), k -> new ArrayList<>());
                if (!record.label().isEmpty()) {
                    labels.add(record.label());
                }
            }
            grouped.put(entry.getKey(), byGroup);
        }
        StringBuilder out = new StringBuilder("{\"scenarios\":{");
        json.appendEntries(out, grouped, (scenarioOut, groups) -> {
            scenarioOut.append("{\"sagas\":{");
            json.appendEntries(scenarioOut, groups, (groupOut, labels) ->
                    groupOut.append("{\"actions\":").append(json.array(labels)).append("}"));
            scenarioOut.append("}}");
        });
        return out.append("}}\n").toString();
    }
}
