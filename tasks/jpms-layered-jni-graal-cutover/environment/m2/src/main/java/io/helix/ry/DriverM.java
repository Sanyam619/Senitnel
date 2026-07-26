package io.helix.ry;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public final class DriverM {
  private DriverM() {}

  public static void main(String[] args) {
    int split = Arrays.asList(args).indexOf("--");
    List<String> reflective;
    List<String> jni;
    if (split < 0) {
      reflective = Arrays.asList(args);
      jni = List.of();
    } else {
      reflective = Arrays.asList(Arrays.copyOfRange(args, 0, split));
      jni = Arrays.asList(Arrays.copyOfRange(args, split + 1, args.length));
    }
    List<Map<String, Object>> rows = sieve_c.apply(reflective, jni);
    System.out.println(sieve_preview.summarize(rows));
    System.out.println(
        rows.stream().map(r -> String.valueOf(r.get("name"))).collect(Collectors.joining(",")));
  }
}
