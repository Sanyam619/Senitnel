package flux;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class OpA {
    private OpA() {}

    public static int op_a(Path a, Path b) {
        try {
            if (a == null) return -1;
            int mode = Q7.W_A;
            List<Map<String, String>> inv = lib.TokenIo.readInventory(a);
            int chosen = -1;

            Set<Integer> rvk = new java.util.HashSet<>();
            if (Q7.W_S == 1) {
                rvk = lib.Journal.revokedEpochs(a.resolve("restore.journal"));
            }

            if (mode == 1) {
                for (Map<String, String> row : inv) {
                    if (Q7.L_C.equals(row.get("role"))) {
                        int e = 0;
                        try { e = Integer.parseInt(row.getOrDefault("epoch", "0")); } catch (Exception ignored) {}
                        if (rvk.contains(e)) continue;
                        chosen = Integer.parseInt(row.get("id"));
                        break;
                    }
                }
            } else if (mode == 2) {
                int fld = Q7.W_G;
                int floor = Q7.W_H;
                int best = -1;
                for (Map<String, String> row : inv) {
                    if (!Q7.L_C.equals(row.get("role"))) continue;
                    int val = 0;
                    if (fld == 1) {
                        try { val = Integer.parseInt(row.getOrDefault("epoch", "0")); } catch (Exception ignored) {}
                    } else if (fld == 2) {
                        try { val = Integer.parseInt(row.getOrDefault("id", "0")); } catch (Exception ignored) {}
                    } else if (fld == 3) {
                        try { val = Integer.parseInt(row.getOrDefault("claimed_lane", "0")); } catch (Exception ignored) {}
                    }
                    if (val < floor) continue;
                    if (fld == 1 && rvk.contains(val)) continue;
                    if (val > best) {
                        best = val;
                        chosen = Integer.parseInt(row.get("id"));
                    }
                }
            } else {
                List<Map<String, String>> objects = lib.TokenIo.readObjects(a);
                boolean preferLowest = Q7.W_F == 1;
                for (Map<String, String> row : objects) {
                    if (!Q7.L_A.equals(row.get("label"))) continue;
                    int id = Integer.parseInt(row.get("slot_id"));
                    if (chosen < 0 || (preferLowest && id < chosen)) {
                        chosen = id;
                    }
                    if (!preferLowest) break;
                }
            }
            if (chosen < 0) return -1;

            String role = null;
            int epoch = 0;
            for (Map<String, String> row : inv) {
                if (Integer.parseInt(row.get("id")) == chosen) {
                    role = row.get("role");
                    try {
                        epoch = Integer.parseInt(row.getOrDefault("epoch", "0"));
                    } catch (Exception ignored) {}
                    break;
                }
            }
            if ("staging".equals(role) && Q7.W_B == 0) return -1;

            if (Q7.W_E == 1) {
                if (!Q7.L_C.equals(role)) return -1;
            }

            lib.TokenIo.writeBound(a, chosen);
            if (Q7.W_C == 1) {
                String nonce = lib.SealUtil.wireNonce(chosen, epoch);
                lib.TokenIo.writeText(a.resolve("wire.nonce"), nonce + "\n");
            } else {
                Files.deleteIfExists(a.resolve("wire.nonce"));
            }
            return 0;
        } catch (Exception e) {
            return -1;
        }
    }
}
