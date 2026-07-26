package io.helix.qx;

public final class DriverP {
  private DriverP() {}

  public static void main(String[] args) {
    String name = args.length > 0 ? args[0] : "io.helix.bridge.NativeHook";
    String prefix = args.length > 1 ? args[1] : "io.helix.internal.bridge";
    System.out.println(fold_b.apply(name, prefix));
    System.out.println(fold_preview.describe(name, prefix));
  }
}
