package lib;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class HandleMap {
    private HandleMap() {}

    public static Map<String, Integer> primaryByLabel(List<Map<String, String>> objects, int slotId) {
        Map<String, Integer> out = new HashMap<>();
        for (Map<String, String> row : objects) {
            if (Integer.parseInt(row.get("slot_id")) != slotId) continue;
            out.put(row.get("label"), Integer.parseInt(row.get("handle")));
        }
        return out;
    }

    public static boolean hasLabelOnSlot(List<Map<String, String>> objects, String label, int slotId) {
        for (Map<String, String> row : objects) {
            if (label.equals(row.get("label")) && Integer.parseInt(row.get("slot_id")) == slotId) {
                return true;
            }
        }
        return false;
    }
}
