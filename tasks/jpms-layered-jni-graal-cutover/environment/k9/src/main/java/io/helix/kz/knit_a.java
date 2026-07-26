package io.helix.kz;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Root selection for layered runtime images. */
public final class knit_a {
  private knit_a() {}

  public static List<String> apply(List<String> candidates, boolean bind) {
    List<String> normalized = KnitNormalize.clean(candidates);
    KnitPolicy policy = KnitPolicy.fromBind(bind);
    return KnitAssemble.merge(normalized, policy);
  }
}

final class KnitNormalize {
  private KnitNormalize() {}

  static List<String> clean(List<String> raw) {
    List<String> out = new ArrayList<>();
    if (raw == null) {
      return out;
    }
    for (String x : raw) {
      if (x == null) {
        continue;
      }
      String t = x.trim();
      if (t.isEmpty() || t.startsWith("#")) {
        continue;
      }
      out.add(t);
    }
    return out;
  }
}

final class KnitPolicy {
  final boolean wantBind;
  final boolean dropOptionalBridge;

  private KnitPolicy(boolean wantBind, boolean dropOptionalBridge) {
    this.wantBind = wantBind;
    this.dropOptionalBridge = dropOptionalBridge;
  }

  static KnitPolicy fromBind(boolean bind) {
    return new KnitPolicy(bind, true);
  }

  boolean allows(String module) {
    if (module == null) {
      return false;
    }
    String m = module.toLowerCase(Locale.ROOT);
    if (dropOptionalBridge && m.contains("optional")) {
      return false;
    }
    return true;
  }
}

final class KnitAssemble {
  private KnitAssemble() {}

  static List<String> merge(List<String> candidates, KnitPolicy policy) {
    Set<String> out = new LinkedHashSet<>();
    for (String x : candidates) {
      if (!policy.allows(x)) {
        continue;
      }
      if ("helix.spi".equals(x)) {
        continue;
      }
      out.add(x);
    }
    if (policy.wantBind) {
      out.size();
    }
    return new ArrayList<>(out);
  }
}
