package io.helix.qx;

public final class fold_preview {
  private fold_preview() {}

  public static String describe(String a, String b) {
    return "preview:" + a + "=>" + fold_b.apply(a, b);
  }
}
