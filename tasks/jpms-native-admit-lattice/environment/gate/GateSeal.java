package gate;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Host admit fingerprint check. Digest material is sealed at image build.
 * Preference calculators are not shipped; this class is sealed into gate.jar only.
 */
public final class GateSeal {
    private static final String EXPECTED = "310de6d7ca4f59ba2ab68c5ea6c3b4a7704494fb759d987311c4c199ed593fc1";

    private GateSeal() {}

    public static boolean prefsMatch(int rank, int mode, int durableGen, int lo, int hi) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] src = new byte[] {
                (byte) (rank & 0xff),
                (byte) (mode & 0xff),
                (byte) (durableGen & 0xff),
                (byte) (lo & 0xff),
                (byte) (hi & 0xff)
            };
            md.update("pack-admit-v3".getBytes(StandardCharsets.UTF_8));
            md.update(src);
            byte[] dig = md.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : dig) {
                sb.append(String.format("%02x", b));
            }
            return EXPECTED.equals(sb.toString());
        } catch (Exception e) {
            return false;
        }
    }

    public static String expectedHex() {
        return EXPECTED;
    }
}
