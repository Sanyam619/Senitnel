package lib;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

public final class Journal {
    private Journal() {}

    public static final String TAG_REVOKE = "01";
    public static final String TAG_CEREMONY = "02";

    public static Set<Integer> revokedEpochs(Path journal) throws IOException {
        Set<Integer> out = new HashSet<>();
        if (journal == null || !Files.exists(journal)) {
            return out;
        }
        for (String ln : Files.readAllLines(journal, StandardCharsets.UTF_8)) {
            ln = ln.trim();
            if (ln.isEmpty() || ln.startsWith("#")) {
                continue;
            }
            String[] parts = ln.split(":", 2);
            if (parts.length != 2) {
                continue;
            }
            if (!TAG_REVOKE.equals(parts[0].trim())) {
                continue;
            }
            try {
                out.add(Integer.parseInt(parts[1].trim(), 16));
            } catch (Exception ignored) {
            }
        }
        return out;
    }

    public static int ceremonyTag(Path journal) throws IOException {
        if (journal == null || !Files.exists(journal)) {
            return 0;
        }
        for (String ln : Files.readAllLines(journal, StandardCharsets.UTF_8)) {
            ln = ln.trim();
            if (ln.isEmpty() || ln.startsWith("#")) {
                continue;
            }
            String[] parts = ln.split(":", 2);
            if (parts.length != 2) {
                continue;
            }
            if (!TAG_CEREMONY.equals(parts[0].trim())) {
                continue;
            }
            try {
                return Integer.parseInt(parts[1].trim(), 16);
            } catch (Exception ignored) {
            }
        }
        return 0;
    }
}
