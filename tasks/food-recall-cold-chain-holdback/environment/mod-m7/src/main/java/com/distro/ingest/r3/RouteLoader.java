package com.distro.ingest.r3;

import com.distro.io.JsonReader;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class RouteLoader {
    public record RouteMeta(long hookTs, long dockTs, List<String> units) {}

    public RouteMeta read(Path path) throws Exception {
        Map<String, Object> m = JsonReader.readObject(path);
        long hook = ((Number) m.get("hook_ts")).longValue();
        long dock = ((Number) m.get("dock_ts")).longValue();
        @SuppressWarnings("unchecked")
        List<String> units = (List<String>) m.get("units");
        return new RouteMeta(hook, dock, units);
    }
}
