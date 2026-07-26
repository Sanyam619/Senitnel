package nest;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class OpB {
    private OpB() {}

    public static int op_b(Path a, Path b, int c) {
        try {
            if (a == null || b == null || c <= 0) return -1;
            if (M3.H_H == 1 && !Files.exists(b)) return -1;

            int bound = lib.TokenIo.readBound(a);
            if (bound < 0) return -1;

            int effectiveTtl = c;
            if (M3.H_F == 1) {
                Path overrideDir = Path.of(M3.HP_D);
                Path slotFile = overrideDir.resolve(bound + ".toml");
                if (Files.exists(slotFile)) {
                    int slotTtl = lib.TokenIo.readPolicyTtl(slotFile);
                    if (slotTtl > 0 && slotTtl < effectiveTtl) {
                        effectiveTtl = slotTtl;
                    }
                }
            }

            List<Map<String, String>> rows = lib.TokenIo.readSessions(a);
            List<Map<String, String>> next = new ArrayList<>();
            for (Map<String, String> row : rows) {
                Map<String, String> m = new HashMap<>(row);
                int sid = Integer.parseInt(m.get("slot_id"));
                if (M3.H_A == 0 || M3.H_C == 1) {
                    m.put("pin_alive", "1");
                    m.put("ttl_sec", Integer.toString(M3.H_G));
                } else if (sid == bound) {
                    m.put("pin_alive", "1");
                    m.put("ttl_sec", Integer.toString(effectiveTtl));
                } else if (M3.H_B == 1) {
                    m.put("pin_alive", "0");
                }
                next.add(m);
            }
            lib.TokenIo.writeSessions(a, next);

            if (M3.H_H == 1) {
                Files.deleteIfExists(b);
            }

            if (M3.H_D == 1) {
                int epoch = 0;
                for (Map<String, String> inv : lib.TokenIo.readInventory(a)) {
                    if (Integer.parseInt(inv.get("id")) == bound) {
                        epoch = Integer.parseInt(inv.getOrDefault("epoch", "0"));
                        break;
                    }
                }

                int tag = 0;
                if (M3.H_Q == 1) {
                    tag = lib.Journal.ceremonyTag(a.resolve("restore.journal"));
                }

                String seal;
                if (M3.H_E == 1) {
                    seal = lib.SealUtil.computeSealV2(bound, epoch, effectiveTtl, tag);
                } else {
                    seal = lib.SealUtil.computeSeal(bound, effectiveTtl);
                }
                lib.TokenIo.writeText(Path.of(M3.HP_C), seal + "\n");
            }

            return 0;
        } catch (Exception e) {
            return -1;
        }
    }
}
