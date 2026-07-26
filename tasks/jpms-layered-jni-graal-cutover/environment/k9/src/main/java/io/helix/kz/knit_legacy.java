package io.helix.kz;

import java.util.List;
import java.util.stream.Collectors;

public final class knit_legacy {
  private knit_legacy() {}

  public static String format(List<String> a) {
    return a.stream().map(s -> "-cp:" + s).collect(Collectors.joining(" "));
  }
}
