package io.helix.qx;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Shared field readers for JSON-ish blobs. */
public final class ParseX {
  private ParseX() {}

  public static String x_str(String raw, String key) {
    Pattern p = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*\"([^\"]*)\"");
    Matcher m = p.matcher(raw);
    if (m.find()) {
      return m.group(1);
    }
    return "";
  }

  public static int x_int(String raw, String key) {
    Pattern p = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*(-?\\d+)");
    Matcher m = p.matcher(raw);
    if (m.find()) {
      return Integer.parseInt(m.group(1));
    }
    return 0;
  }

  public static long x_long(String raw, String key) {
    Pattern p = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*(-?\\d+)");
    Matcher m = p.matcher(raw);
    if (m.find()) {
      return Long.parseLong(m.group(1));
    }
    return 0L;
  }

  /** Reads spi_by_root.<root> from roots material. */
  public static String x_str_by_root(String roots, String root) {
    Pattern p = Pattern.compile(
        "\"spi_by_root\"\\s*:\\s*\\{[^}]*\"" + Pattern.quote(root) + "\"\\s*:\\s*\"([^\"]*)\"");
    Matcher m = p.matcher(roots);
    if (m.find()) {
      return m.group(1);
    }
    return "";
  }

  /** Reads roots.<root>.generation */
  public static int x_int_nested(String roots, String root, String field) {
    Pattern block = Pattern.compile(
        "\"" + Pattern.quote(root) + "\"\\s*:\\s*\\{([^}]*)\\}");
    Matcher mb = block.matcher(roots);
    if (!mb.find()) {
      return 0;
    }
    return x_int("{" + mb.group(1) + "}", field);
  }
}
