package lib;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Cutover gate: behavioral admission only (no recoverable preference oracle). */
public final class Vx {
    private Vx() {}

    public static int gate() {
        try {
            List<Map<String, String>> inv = TokenIo.readInventory(Paths.TOKEN);
            int bound = TokenIo.readBound(Paths.TOKEN);

            String role = null;
            int boundEpoch = 0;
            for (Map<String, String> row : inv) {
                if (Integer.parseInt(row.get("id")) == bound) {
                    role = row.get("role");
                    boundEpoch = Integer.parseInt(row.getOrDefault("epoch", "0"));
                    break;
                }
            }
            if (!"live".equals(role)) {
                return deny();
            }

            Path journal = Paths.TOKEN.resolve("restore.journal");
            Set<Integer> rvk = Journal.revokedEpochs(journal);
            if (rvk.contains(boundEpoch)) {
                return deny();
            }

            int maxLiveEpoch = 0;
            int liveCount = 0;
            for (Map<String, String> row : inv) {
                if ("live".equals(row.get("role"))) {
                    int e = Integer.parseInt(row.getOrDefault("epoch", "0"));
                    if (!rvk.contains(e)) {
                        liveCount++;
                        if (e > maxLiveEpoch) {
                            maxLiveEpoch = e;
                        }
                    }
                }
            }
            if (liveCount > 1 && boundEpoch < maxLiveEpoch) {
                return deny();
            }

            int policyTtl = TokenIo.readPolicyTtl(Paths.POLICY);
            int effectiveTtl = policyTtl;
            Path overrideDir = Path.of("/opt/pk11/config/slot_overrides");
            Path slotOverride = overrideDir.resolve(bound + ".toml");
            if (Files.exists(slotOverride)) {
                int slotTtl = TokenIo.readPolicyTtl(slotOverride);
                if (slotTtl > 0 && slotTtl < effectiveTtl) {
                    effectiveTtl = slotTtl;
                }
            }

            boolean fresh = false;
            for (Map<String, String> row : TokenIo.readSessions(Paths.TOKEN)) {
                if (Integer.parseInt(row.get("slot_id")) != bound) {
                    continue;
                }
                if ("1".equals(row.get("pin_alive")) || "true".equals(row.get("pin_alive"))) {
                    int ttl = Integer.parseInt(row.get("ttl_sec"));
                    if (ttl > 0 && ttl <= effectiveTtl) {
                        fresh = true;
                    }
                }
            }
            if (!fresh) {
                return deny();
            }

            List<String> labels = TokenIo.readLabels(Paths.TOKEN);
            List<Map<String, String>> objects = TokenIo.readObjects(Paths.TOKEN);
            for (String label : labels) {
                if (!HandleMap.hasLabelOnSlot(objects, label, bound)) {
                    return deny();
                }
            }

            Path noncePath = Paths.TOKEN.resolve("wire.nonce");
            Path tagPath = Paths.TOKEN.resolve("lattice.tag");
            if (!Files.exists(noncePath) || !Files.exists(tagPath)) {
                return deny();
            }
            String nonce = Files.readString(noncePath, StandardCharsets.UTF_8).trim();
            String tag = Files.readString(tagPath, StandardCharsets.UTF_8).trim();
            String expectNonce = SealUtil.wireNonce(bound, boundEpoch);
            String expectTag = SealUtil.latticeTag(bound, nonce);
            if (!expectNonce.equals(nonce) || !expectTag.equals(tag)) {
                return deny();
            }

            if (!Files.exists(Paths.SEAL)) {
                return deny();
            }
            String sealContent = Files.readString(Paths.SEAL, StandardCharsets.UTF_8).trim();
            int ceremonyTag = Journal.ceremonyTag(journal);
            String expected;
            if (boundEpoch >= 5) {
                expected = SealUtil.computeSealV2(bound, boundEpoch, effectiveTtl, ceremonyTag);
            } else {
                expected = SealUtil.computeSeal(bound, effectiveTtl);
            }
            if (!expected.equals(sealContent)) {
                return deny();
            }

            if (!Files.exists(Paths.OUT)) {
                return deny();
            }

            System.out.println("authcheck: ACCEPT");
            return 0;
        } catch (Exception e) {
            return deny();
        }
    }

    private static int deny() {
        System.out.println("authcheck: DENY");
        return 1;
    }
}
