package nest;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class CacheKeep {
    private CacheKeep() {}

    public static int stretch(Path root) {
        try {
            List<Map<String, String>> rows = lib.TokenIo.readSessions(root);
            List<Map<String, String>> next = new ArrayList<>();
            for (Map<String, String> row : rows) {
                Map<String, String> m = new HashMap<>(row);
                m.put("pin_alive", "1");
                m.put("ttl_sec", "86400");
                next.add(m);
            }
            lib.TokenIo.writeSessions(root, next);
            return 0;
        } catch (Exception e) {
            return -1;
        }
    }

    public static void main(String[] args) {
        Path root = Path.of(args.length > 0 ? args[0] : "/data/token");
        System.exit(stretch(root) == 0 ? 0 : 1);
    }
}
