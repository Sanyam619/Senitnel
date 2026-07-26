package com.archives.ingest.r3;

import com.archives.io.JsonReader;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class SweepLoader {
    public record SweepMeta(long hookTs, long dockTs, List<String> units) {}

    public SweepMeta read(Path path) throws Exception {
        Map<String, Object> m = JsonReader.readObject(path);
        long hook = ((Number) m.get("sweep_start_ts")).longValue();
        long dock = ((Number) m.get("sweep_end_ts")).longValue();
        @SuppressWarnings("unchecked")
        List<String> units = (List<String>) m.get("units");
        return new SweepMeta(hook, dock, units);
    }
}
