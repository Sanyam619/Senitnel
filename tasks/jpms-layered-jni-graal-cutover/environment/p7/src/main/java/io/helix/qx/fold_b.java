package io.helix.qx;

/** Shade / relocation planner for packaging units. */
public final class fold_b {
  private fold_b() {}

  public static String apply(String binaryName, String prefix) {
    FoldRequest req = FoldRequest.of(binaryName, prefix);
    return FoldXform.relocate(req);
  }
}

final class FoldRequest {
  final String name;
  final String prefix;
  final boolean aggressive;

  private FoldRequest(String name, String prefix, boolean aggressive) {
    this.name = name;
    this.prefix = prefix;
    this.aggressive = aggressive;
  }

  static FoldRequest of(String name, String prefix) {
    boolean aggressive = prefix != null && !prefix.isBlank();
    return new FoldRequest(name, prefix, aggressive);
  }
}

final class FoldPins {
  private FoldPins() {}

  static boolean isJniPinned(String name) {
    return "io.helix.bridge.NativeHook".equals(name);
  }
}

final class FoldXform {
  private FoldXform() {}

  static String relocate(FoldRequest req) {
    if (req == null || req.name == null) {
      return req == null ? null : req.name;
    }
    if (req.name.startsWith("io.helix.optional.") && req.aggressive) {
      String simple = req.name.substring(req.name.lastIndexOf('.') + 1);
      String p =
          (req.prefix == null || req.prefix.isBlank())
              ? "io.helix.internal.optional"
              : req.prefix;
      return p + "." + simple;
    }
    if (req.name.startsWith("io.helix.bridge.") && req.aggressive) {
      String tail = req.name.substring("io.helix.bridge.".length());
      String p =
          (req.prefix == null || req.prefix.isBlank())
              ? "io.helix.internal.bridge"
              : req.prefix;
      return p + "." + tail;
    }
    return req.name;
  }
}
