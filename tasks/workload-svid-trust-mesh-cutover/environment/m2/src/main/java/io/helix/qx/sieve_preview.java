package io.helix.qx;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Collectors;

/** Lists KeyStore-style alias lines for diagnostics without rebuilding trust. */
public final class sieve_preview {
  private sieve_preview() {}

  public static String apply(String a) {
    try {
      Path p = Path.of(a);
      if (!Files.isRegularFile(p)) {
        return "";
      }
      return Files.lines(p).limit(8).collect(Collectors.joining(","));
    } catch (Exception e) {
      return "";
    }
  }

  public static void main(String[] args) {
    String path = args.length > 0 ? args[0] : "/app/data/material/roots.json";
    System.out.println(apply(path));
  }
}
