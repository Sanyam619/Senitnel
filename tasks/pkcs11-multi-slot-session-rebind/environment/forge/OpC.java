package forge;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class OpC {
    private OpC() {}

    public static int op_c(Path a, Path b, Path c) {
        try {
            if (a == null || c == null) return -1;

            int bound;
            if (P9.S_D == 0) {
                Path overridePath = Path.of(P9.SP_A);
                if (Files.exists(overridePath)) {
                    bound = lib.TokenIo.readBoundFromFile(overridePath);
                } else {
                    bound = lib.TokenIo.readBound(a);
                }
            } else if (P9.S_T == 1) {
                Path fallbackPath = Path.of(P9.SP_B);
                if (Files.exists(fallbackPath)) {
                    bound = lib.TokenIo.readBoundFromFile(fallbackPath);
                } else {
                    bound = lib.TokenIo.readBound(a);
                }
            } else {
                bound = lib.TokenIo.readBound(a);
            }

            List<Map<String, String>> inv = lib.TokenIo.readInventory(a);
            List<Map<String, String>> objects = lib.TokenIo.readObjects(a);
            List<String> labels = lib.TokenIo.readLabels(a);
            Set<String> want = new HashSet<>(labels);

            Map<Integer, String> roles = new HashMap<>();
            for (Map<String, String> row : inv) {
                roles.put(Integer.parseInt(row.get("id")), row.get("role"));
            }

            List<Map<String, String>> slots = new ArrayList<>();
            for (Map<String, String> row : inv) {
                Map<String, String> s = new HashMap<>();
                int id = Integer.parseInt(row.get("id"));
                s.put("id", Integer.toString(id));
                s.put("role", row.get("role"));
                s.put("provider_bound", id == bound ? "true" : "false");
                slots.add(s);
            }

            List<Map<String, String>> sessions = new ArrayList<>();
            for (Map<String, String> row : lib.TokenIo.readSessions(a)) {
                Map<String, String> s = new HashMap<>();
                s.put("slot_id", row.get("slot_id"));
                String fresh = row.get("pin_alive");
                boolean pf = "1".equals(fresh) || "true".equalsIgnoreCase(fresh);
                s.put("pin_alive", pf ? "true" : "false");
                s.put("ttl_sec", row.get("ttl_sec"));
                sessions.add(s);
            }

            List<Map<String, String>> certs = new ArrayList<>();
            for (Map<String, String> row : objects) {
                String label = row.get("label");
                if (!want.contains(label)) continue;
                int sid = Integer.parseInt(row.get("slot_id"));
                String role = roles.getOrDefault(sid, "");
                if ("staging".equals(role) && P9.S_B == 0) continue;
                Map<String, String> out = new HashMap<>();
                out.put("label", label);
                out.put("slot_id", Integer.toString(sid));
                boolean auth;
                if (P9.S_A == 1 || P9.S_C == 1) {
                    auth = sid == bound;
                } else {
                    auth = true;
                }
                out.put("handle_auth", auth ? "true" : "false");
                certs.add(out);
            }

            lib.JsonOut.writeLedger(c, slots, sessions, certs);

            if (P9.S_E == 1) {
                Path noncePath = a.resolve("wire.nonce");
                if (!Files.exists(noncePath)) {
                    return -1;
                }
                String nonce = Files.readString(noncePath).trim();
                String tag = lib.SealUtil.latticeTag(bound, nonce);
                lib.TokenIo.writeText(a.resolve("lattice.tag"), tag + "\n");
            } else {
                Files.deleteIfExists(a.resolve("lattice.tag"));
            }
            return 0;
        } catch (Exception e) {
            return -1;
        }
    }
}
