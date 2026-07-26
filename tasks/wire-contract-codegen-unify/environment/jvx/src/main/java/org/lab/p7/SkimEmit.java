package org.lab.p7;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** Maven BOM skim used by Java lanehealth; emits locally consistent skim rows. */
public final class SkimEmit {
    private SkimEmit() {}

    public static List<EmitC.Row> read(String root) {
        String reg = (root == null || root.isEmpty()) ? "/app/data/registry" : root;
        try {
            String meta = Files.readString(Path.of(reg, "plugin_meta.json"), StandardCharsets.UTF_8);
            String skim = EmitC.extractString(meta, "skim_key");
            if (skim == null) {
                skim = "pg-core@0.9.0";
            }
            return EmitC.parseSlots(EmitC.pluginBlock(meta, skim));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
