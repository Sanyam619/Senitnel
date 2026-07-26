package findscan;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class Main {
    public static void main(String[] args) throws Exception {
        List<String> labels = lib.TokenIo.readLabels(lib.Paths.TOKEN);
        List<Map<String, String>> objects = lib.TokenIo.readObjects(lib.Paths.TOKEN);
        Map<String, Integer> counts = new HashMap<>();
        for (String label : labels) {
            counts.put(label, 0);
        }
        for (Map<String, String> row : objects) {
            String label = row.get("label");
            if (counts.containsKey(label)) {
                counts.put(label, counts.get(label) + 1);
            }
        }
        boolean ok = true;
        for (Map.Entry<String, Integer> e : counts.entrySet()) {
            System.out.println(e.getKey() + " count=" + e.getValue());
            if (e.getValue() < 1) ok = false;
        }
        if (ok) {
            System.out.println("findscan: OK");
            System.exit(0);
        }
        System.out.println("findscan: MISS");
        System.exit(1);
    }
}
