package lib;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public final class SealUtil {
    private SealUtil() {}

    public static String preferenceDigest() {
        String raw = String.join(
                ":",
                Integer.toString(flux.Q7.W_A),
                Integer.toString(flux.Q7.W_B),
                Integer.toString(flux.Q7.W_C),
                Integer.toString(flux.Q7.W_D),
                Integer.toString(flux.Q7.W_E),
                Integer.toString(flux.Q7.W_F),
                Integer.toString(flux.Q7.W_G),
                Integer.toString(flux.Q7.W_H),
                Integer.toString(flux.Q7.W_S),
                Integer.toString(nest.M3.H_A),
                Integer.toString(nest.M3.H_B),
                Integer.toString(nest.M3.H_C),
                Integer.toString(nest.M3.H_D),
                Integer.toString(nest.M3.H_E),
                Integer.toString(nest.M3.H_F),
                Integer.toString(nest.M3.H_H),
                Integer.toString(nest.M3.H_Q),
                Integer.toString(forge.P9.S_A),
                Integer.toString(forge.P9.S_B),
                Integer.toString(forge.P9.S_C),
                Integer.toString(forge.P9.S_D),
                Integer.toString(forge.P9.S_E),
                Integer.toString(forge.P9.S_T));
        return hex16(raw);
    }

    public static String wireNonce(int boundId, int epoch) {
        return hex16("wire:" + boundId + ":" + epoch);
    }

    public static String latticeTag(int boundId, String wireNonce) {
        return hex16(preferenceDigest() + ":" + boundId + ":" + wireNonce);
    }

    public static String computeSeal(int boundId, int policyTtl) {
        try {
            String input = "rebind:" + boundId + ":" + policyTtl + ":" + preferenceDigest();
            return hex16Digest(input);
        } catch (Exception e) {
            return "";
        }
    }

    public static String computeSealV2(int boundId, int epoch, int policyTtl, int tag) {
        try {
            int salt = tag ^ boundId;
            String input = "rebind-v3:" + boundId + ":" + epoch + ":"
                    + policyTtl + ":" + Integer.toHexString(salt)
                    + ":" + preferenceDigest();
            return hex16Digest(input);
        } catch (Exception e) {
            return "";
        }
    }

    private static String hex16(String input) {
        try {
            return hex16Digest(input);
        } catch (Exception e) {
            return "";
        }
    }

    private static String hex16Digest(String input) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] hash = md.digest(input.getBytes(StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 8; i++) {
            sb.append(String.format("%02x", hash[i]));
        }
        return sb.toString();
    }
}
