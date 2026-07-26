package lib;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

public final class CaseIo {
    private CaseIo() {}

    public static List<Map<String, Object>> loadCases() throws IOException {
        List<Map<String, Object>> out = new ArrayList<>();
        try (DirectoryStream<Path> ds = Files.newDirectoryStream(Paths.CASES, "*.json")) {
            Set<Path> sorted = new TreeSet<>();
            for (Path p : ds) {
                sorted.add(p);
            }
            for (Path p : sorted) {
                out.add(parseLoose(Files.readString(p)));
            }
        }
        return out;
    }

    public static Set<String> loadMarks() throws IOException {
        Path marks = Paths.REVOKE.resolve("marks.rl");
        Set<String> out = new TreeSet<>();
        if (!Files.exists(marks)) {
            return out;
        }
        for (String line : Files.readString(marks).split("\n")) {
            line = line.trim();
            if (!line.isEmpty() && !line.startsWith("#")) {
                out.add(line);
            }
        }
        return out;
    }

    public static int[] loadWindow() throws IOException {
        Path win = Paths.REVOKE.resolve("window.toml");
        int lo = 0;
        int hi = 0;
        for (String line : Files.readString(win).split("\n")) {
            line = line.trim();
            if (line.startsWith("lo")) {
                lo = Integer.parseInt(line.split("=", 2)[1].trim());
            } else if (line.startsWith("hi")) {
                hi = Integer.parseInt(line.split("=", 2)[1].trim());
            }
        }
        return new int[] {lo, hi};
    }

    public static int readBundleGen(Path bundle) throws IOException {
        byte[] b = Files.readAllBytes(bundle);
        if (b.length < 5) {
            return -1;
        }
        return b[4] & 0xff;
    }

    public static int runtimeEpoch() throws IOException {
        String s = Files.readString(Paths.RUNTIME);
        int colon = s.indexOf(':');
        String num = s.substring(colon + 1).replaceAll("[^0-9]", "");
        return Integer.parseInt(num);
    }

    static Map<String, Object> parseLoose(String text) {
        Map<String, Object> m = new LinkedHashMap<>();
        String body = text.trim();
        if (body.startsWith("{")) {
            body = body.substring(1);
        }
        if (body.endsWith("}")) {
            body = body.substring(0, body.length() - 1);
        }
        for (String part : body.split(",")) {
            String[] kv = part.split(":", 2);
            if (kv.length != 2) {
                continue;
            }
            String k = kv[0].trim().replace("\"", "");
            String v = kv[1].trim();
            if (v.startsWith("\"") && v.endsWith("\"")) {
                m.put(k, v.substring(1, v.length() - 1));
            } else {
                m.put(k, Integer.parseInt(v));
            }
        }
        return m;
    }
}
