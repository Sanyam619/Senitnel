package io.helix.ry;

import java.util.List;
import java.util.Map;

public final class sieve_preview {
  private sieve_preview() {}

  public static int count(List<String> a, List<String> b) {
    return sieve_c.apply(a, b).size();
  }

  public static String summarize(List<Map<String, Object>> rows) {
    return "rows=" + rows.size();
  }
}
