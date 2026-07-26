package slotprobe;

import java.util.List;
import java.util.Map;

public final class Main {
    public static void main(String[] args) throws Exception {
        List<Map<String, String>> inv = lib.TokenIo.readInventory(lib.Paths.TOKEN);
        int bound = lib.TokenIo.readBound(lib.Paths.TOKEN);
        System.out.println("bound=" + bound);
        for (Map<String, String> row : inv) {
            System.out.println("slot id=" + row.get("id") + " role=" + row.get("role"));
        }
        List<Map<String, String>> sessions = lib.TokenIo.readSessions(lib.Paths.TOKEN);
        for (Map<String, String> row : sessions) {
            System.out.println(
                    "ctx slot=" + row.get("slot_id")
                            + " pin=" + row.get("pin_alive")
                            + " ttl=" + row.get("ttl_sec"));
        }
    }
}
