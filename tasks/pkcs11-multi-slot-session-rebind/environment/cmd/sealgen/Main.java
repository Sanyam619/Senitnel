package sealgen;

import java.nio.file.Path;
import java.util.Map;

public final class Main {
    public static void main(String[] args) throws Exception {
        int bound = lib.TokenIo.readBound(lib.Paths.TOKEN);
        int ttl = lib.TokenIo.readPolicyTtl(lib.Paths.POLICY);

        Path overrideDir = Path.of("/opt/pk11/config/slot_overrides");
        Path slotFile = overrideDir.resolve(bound + ".toml");
        if (slotFile.toFile().exists()) {
            int slotTtl = lib.TokenIo.readPolicyTtl(slotFile);
            if (slotTtl > 0 && slotTtl < ttl) {
                ttl = slotTtl;
            }
        }

        int epoch = 0;
        for (Map<String, String> row : lib.TokenIo.readInventory(lib.Paths.TOKEN)) {
            if (Integer.parseInt(row.get("id")) == bound) {
                epoch = Integer.parseInt(row.getOrDefault("epoch", "0"));
                break;
            }
        }

        int ceremonyTag = lib.Journal.ceremonyTag(lib.Paths.TOKEN.resolve("restore.journal"));

        String seal;
        if (epoch >= 5) {
            seal = lib.SealUtil.computeSealV2(bound, epoch, ttl, ceremonyTag);
        } else {
            seal = lib.SealUtil.computeSeal(bound, ttl);
        }
        lib.TokenIo.writeText(lib.Paths.SEAL, seal + "\n");
        System.out.println("sealgen: " + seal);
    }
}
