package io.helix.qx;

import java.nio.file.Files;
import java.nio.file.Path;

/** Cache view helper for diagnostics. */
public final class CacheView {
  private CacheView() {}

  public static boolean isWarm(String path) {
    try {
      String raw = Files.readString(Path.of(path));
      return raw.contains("\"warm\": true") || raw.contains("\"warm\":true");
    } catch (Exception e) {
      return false;
    }
  }
}
